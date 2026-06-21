#!/usr/bin/env python3
"""Apply documentation status changes from docs/audit_status.md.

Reads each .md file, updates the `status` field in YAML frontmatter,
or adds frontmatter if missing.
"""

import os
import re
import sys

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')

# Mapping: filename (relative to docs/) -> new_status
# If new_status is None, skip (no change needed)
MAPPING = {
    # === 3.1 DRAFT -> ACTIVE ===
    '008_PRM_BUILD_AGENT_1_0_DRAFT.md': 'ACTIVE',
    '029_PROP_DOC_DOCS_ORGANIZATION_1_0_DRAFT.md': 'ACTIVE',
    'ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md': 'ACTIVE',
    'onboarding/README.md': 'ACTIVE',
    'onboarding/01_pipeline.md': 'ACTIVE',
    'onboarding/02_new_stage.md': 'ACTIVE',
    'onboarding/03_testing.md': 'ACTIVE',
    'onboarding/04_debugging.md': 'ACTIVE',
    'architecture/001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/001_CLASS_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/001_CLASS_DIAGRAM_ASCII_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/002_USECASE_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/003_SEQUENCE_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/004_ACTIVITY_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/005_STATEMACHINE_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/006_COMPONENT_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/007_DEPLOYMENT_DIAGRAM_RECPL_1_0_DRAFT.md': 'ACTIVE',
    'diagrams/008_CLASS_DIAGRAM_RECPL_Chatgpt_1_0_DRAFT_.md': 'ACTIVE',
    '152_GUIDE_DEV_AGENT_DESIGN_PATTERNS_SUMMARY_1_0_DRAFT.md': 'ACTIVE',
    '153_GUIDE_DEV_AGENT_DESIGN_PATTERNS2_SUMMARY_1_0_DRAFT.md': 'ACTIVE',
    '104_GUIDE_DEV_AGENT_RUNBOOK_1_0_DRAFT.md': 'ACTIVE',
    '176_GUIDE_OPS_PDCA_SDLC_EVENTBUS_DASHBOARD_1_0_DRAFT.md': 'ACTIVE',
    'archive/070_GUIDE_DEV_PYTHON_STYLE_1_0_DRAFT.md': 'ACTIVE',

    # === 3.2 ACTIVE -> DRAFT ===
    '041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md': 'DRAFT',

    # === 3.3 Plans DRAFT -> IMPLEMENTED ===
    '067_PLAN_DEV_COMPILER_BOT_SCALE_IMPL_1_0_DRAFT.md': 'IMPLEMENTED',
    '093_PLAN_DEV_SPRINT16_1_0_DRAFT.md': 'IMPLEMENTED',
    '100_PLAN_DEV_AGENT_EXECUTION_1_0_DRAFT.md': 'IMPLEMENTED',
    '106_PLAN_DEV_PROMPT_CHAIN_EXECUTION_1_0_DRAFT.md': 'IMPLEMENTED',
    '116_PLAN_DEV_BEHAVIORAL_PATTERNS_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '122_PLAN_DEV_PATTERNS_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '123_PLAN_DEV_PATTERNS_ACTION_1_0_DRAFT.md': 'IMPLEMENTED',
    '126_PLAN_DEV_PIPELINE_FIXES_1_0_DRAFT.md': 'IMPLEMENTED',
    '138_PLAN_DEV_METRICS_DASHBOARD_VERSION_ALIGNMENT_EXECUTION_1_0_DRAFT.md': 'IMPLEMENTED',
    '149_PLAN_DEV_REMAINING_ARCHITECTURAL_ITEMS_1_0_DRAFT.md': 'IMPLEMENTED',
    '157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md': 'IMPLEMENTED',
    '158_PLAN_DEV_PDCA_SDLC_EXECUTION_1_0_DRAFT.md': 'IMPLEMENTED',
    '169_PLAN_DEV_PDCA_SDLC_DASHBOARD_1_0_DRAFT.md': 'IMPLEMENTED',
    '172_PLAN_DEV_PDCA_SDLC_EVENTBUS_API_EXECUTION_1_0_DRAFT.md': 'IMPLEMENTED',

    # === 3.4 Proposals DRAFT -> IMPLEMENTED ===
    '066_PROP_DEV_COMPILER_BOT_SCALE_VISION_1_0_DRAFT.md': 'IMPLEMENTED',
    '085_PROP_DEV_PIPELINE_DEBUG_REFINE_1_0_DRAFT.md': 'IMPLEMENTED',
    '087_PROP_DEV_NLP_INTENT_PIPELINE_1_0_DRAFT.md': 'IMPLEMENTED',
    '092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION_1_0_DRAFT.md': 'IMPLEMENTED',
    '099_PROP_DEV_AGENT_VISION_1_0_DRAFT.md': 'IMPLEMENTED',
    '105_PROP_DEV_PROMPT_CHAIN_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '120_PROP_DEV_DASHBOARD_MVP_1_0_DRAFT.md': 'IMPLEMENTED',
    '121_PLAN_DEV_ARCHITECTURAL_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '137_PROP_DEV_METRICS_DASHBOARD_AND_VERSION_ALIGNMENT_1_0_DRAFT.md': 'IMPLEMENTED',

    # === 3.5 Reports DRAFT -> IMPLEMENTED ===
    '086_REP_DEV_DEBUGGER_RUNBOOK_1_0_DRAFT.md': 'IMPLEMENTED',
    '089_REP_DEV_SPRINT15_FASE1_2_1_0_DRAFT.md': 'IMPLEMENTED',
    '090_REP_DEV_SPRINT15_FASE3_1_0_DRAFT.md': 'IMPLEMENTED',
    '091_REP_MGT_MULTI_PERSPECTIVE_ANALYSIS_1_0_DRAFT.md': 'IMPLEMENTED',
    '094_REP_DEV_TRACK_ABC_1_0_DRAFT.md': 'IMPLEMENTED',
    '096_REP_DEV_TRACK_D_1_0_DRAFT.md': 'IMPLEMENTED',
    '097_REP_DEV_TRACK_E_1_0_DRAFT.md': 'IMPLEMENTED',
    '098_REP_DEV_TRACK_F_1_0_DRAFT.md': 'IMPLEMENTED',
    '101_REP_DEV_AGENT_N1_1_0_DRAFT.md': 'IMPLEMENTED',
    '102_REP_DEV_AGENT_N2_1_0_DRAFT.md': 'IMPLEMENTED',
    '103_REP_DEV_AGENT_N3_1_0_DRAFT.md': 'IMPLEMENTED',
    '107_REP_DEV_PROMPT_CHAIN_F1_1_0_DRAFT.md': 'IMPLEMENTED',
    '108_REP_DEV_PROMPT_CHAIN_F2_1_0_DRAFT.md': 'IMPLEMENTED',
    '109_REP_DEV_PROMPT_CHAIN_F3_1_0_DRAFT.md': 'IMPLEMENTED',
    '110_REP_DEV_PROMPT_CHAIN_F4_1_0_DRAFT.md': 'IMPLEMENTED',
    '111_REP_DEV_PROMPT_CHAIN_F5_1_0_DRAFT.md': 'IMPLEMENTED',
    '112_REP_DEV_BUGS_FIXES_1_0_DRAFT.md': 'IMPLEMENTED',
    '113_REP_DEV_STATE_VS_LESSONS_1_0_DRAFT.md': 'IMPLEMENTED',
    '114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md': 'IMPLEMENTED',
    '117_REP_DEV_FASE1_COR_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '118_REP_DEV_FASE2_COMMAND_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '119_REP_DEV_FASE3_OBSERVER_REFACTOR_1_0_DRAFT.md': 'IMPLEMENTED',
    '124_REP_DEV_PATTERNS_ACTION_TRACK-A_1_0_DRAFT.md': 'IMPLEMENTED',
    '125_REP_DEV_PATTERNS_ACTION_TRACK-B_1_0_DRAFT.md': 'IMPLEMENTED',
    '128_REP_DEV_PIPELINE_FIXES_VERIFICATION_1_0_DRAFT.md': 'IMPLEMENTED',
    '131_REP_DEV_M0_EXECUTION_REPORT_1_0_DRAFT.md': 'IMPLEMENTED',
    '132_REP_DEV_M1_EXECUTION_REPORT_1_0_DRAFT.md': 'IMPLEMENTED',
    '133_REP_DEV_M2_EXECUTION_REPORT_1_0_DRAFT.md': 'IMPLEMENTED',
    '134_REP_DEV_M3_EXECUTION_REPORT_1_0_DRAFT.md': 'IMPLEMENTED',
    '135_REP_DEV_M4_EXECUTION_REPORT_1_0_DRAFT.md': 'IMPLEMENTED',
    '139_REP_DEV_FASE1_VERSION_ALIGNMENT_1_0_DRAFT.md': 'IMPLEMENTED',
    '139_REP_DEV_PHASE0_PREPARATION_METRICS_DASHBOARD_1_0_DRAFT.md': 'IMPLEMENTED',
    '140_REP_DEV_FASE2_VERSION_CHECK_SCRIPT_1_0_DRAFT.md': 'IMPLEMENTED',
    '141_REP_DEV_FASE3_CI_INTEGRATION_1_0_DRAFT.md': 'IMPLEMENTED',
    '142_REP_DEV_FASE4_DASHBOARD_SERVICE_1_0_DRAFT.md': 'IMPLEMENTED',
    '143_REP_DEV_FASE5_HTTP_SERVER_1_0_DRAFT.md': 'IMPLEMENTED',
    '144_REP_DEV_FASE6_CLI_DASHBOARD_1_0_DRAFT.md': 'IMPLEMENTED',
    '145_REP_DEV_FASE7_STATIC_UI_1_0_DRAFT.md': 'IMPLEMENTED',
    '146_REP_DEV_FASE8_OPERATIONAL_DOCS_1_0_DRAFT.md': 'IMPLEMENTED',
    '147_REP_DEV_FASE9_DAILY_GATE_1_0_DRAFT.md': 'IMPLEMENTED',
    '148_REP_DEV_FASE10_RELEASE_GATE_1_0_DRAFT.md': 'IMPLEMENTED',
    '150_REP_DEV_P4_THREAD_SAFE_STAGESUBJECT_1_0_DRAFT.md': 'IMPLEMENTED',
    '151_REP_DEV_P5_EVENTBUS_UNIFICATION_1_0_DRAFT.md': 'IMPLEMENTED',
    '154_PROP_DEV_ISO12207_AGENT_SYSTEM_ANALYSIS_1_0_DRAFT.md': 'IMPLEMENTED',
    '155_PROP_DEV_ISO12207_AGENT_SYSTEM_REACTIVE_VISION_1_0_DRAFT.md': 'IMPLEMENTED',
    '156_PROP_DEV_ISO12207_AGENT_SYSTEM_ARCHITECT_IMPL_1_0_DRAFT.md': 'IMPLEMENTED',
    '159_REP_DEV_PDCA_SDLC_F1_EXECUTION_1_0_DRAFT.md': 'IMPLEMENTED',
    '161_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '162_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '163_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '164_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '165_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '166_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '167_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '168_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md': 'IMPLEMENTED',
    '170_REP_DEV_PDCA_SDLC_DASHBOARD_1_0_DRAFT.md': 'IMPLEMENTED',
    '171_ANALYSIS_DEV_PDCA_SDLC_EVENTBUS_API_1_0_DRAFT.md': 'IMPLEMENTED',
    '173_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_A_1_0_DRAFT.md': 'IMPLEMENTED',
    '174_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_B_1_0_DRAFT.md': 'IMPLEMENTED',
    '175_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_C_1_0_DRAFT.md': 'IMPLEMENTED',
    '177_REP_DEV_PDCA_SDLC_DASHBOARD_FIXES_1_0_DRAFT.md': 'IMPLEMENTED',
    '178_ANALYSIS_DEV_COMPREHENSIVE_TECHNICAL_REPORT_1_0_DRAFT.md': 'IMPLEMENTED',

    # === 3.6 Archive sprints DRAFT -> IMPLEMENTED ===
    'archive/069_REP_DEV_COMPILER_BOT_SPRINT1_FOUNDATION_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/071_REP_DEV_COMPILER_BOT_SPRINT2_REQUIREMENT_DECOMPOSER_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/072_REP_DEV_COMPILER_BOT_SPRINT3_PREPROCESSOR_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/073_REP_DEV_COMPILER_BOT_SPRINT4_LEXER_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/074_REP_DEV_COMPILER_BOT_SPRINT5_PARSER_GLR_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/075_REP_DEV_COMPILER_BOT_SPRINT6_SEMANTIC_ANALYZER_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/076_REP_DEV_COMPILER_BOT_SPRINT7_IR_GENERATOR_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/077_REP_DEV_COMPILER_BOT_SPRINT8_PLANNER_HIBRIDO_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/078_REP_DEV_COMPILER_BOT_SPRINT9_SYNTHESIS_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/079_REP_DEV_COMPILER_BOT_SPRINT10_VALIDATOR_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/080_REP_DEV_COMPILER_BOT_SPRINT11_UI_GENERATOR_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/081_REP_DEV_COMPILER_BOT_SPRINT12_FEEDBACK_1_0_DRAFT.md': 'IMPLEMENTED',
    'archive/082_REP_DEV_COMPILER_BOT_SPRINT13_BETA_1_0_DRAFT.md': 'IMPLEMENTED',

    # === 3.8 DRAFT -> OBSOLETE (v1.0 superseded by v1.1) ===
    '094_REP_DEV_TRACK_AB_1_0_DRAFT.md': 'OBSOLETE',
}

# Files without frontmatter that need it added
FILES_WITHOUT_FRONTMATTER = {
    '082_REP_DEV_PROJECT0_COMPREHENSIVE_ANALYSIS_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'PROJECT',
        'version': '1.0',
    },
    '127_PROP_DEV_PIPELINE_HTTP_WRAPPER_1_0_DRAFT.md': {
        'status': 'DRAFT',
        'area': 'dev',
        'type': 'PROP',
        'module': 'agentic_pipeline',
        'version': '1.0',
    },
    '128_REP_DEV_PIPELINE_FIXES_VERIFICATION_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'agentic_pipeline',
        'version': '1.0',
    },
    '129_PROP_DEV_ARCHITECTURAL_MIGRATION_1_0_DRAFT.md': {
        'status': 'DRAFT',
        'area': 'dev',
        'type': 'PROP',
        'module': 'agentic_pipeline',
        'version': '1.0',
    },
    '130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md': {
        'status': 'DRAFT',
        'area': 'dev',
        'type': 'PLAN',
        'module': 'agentic_pipeline',
        'version': '1.0',
    },
    'offline_mode.md': {
        'status': 'ACTIVE',
        'area': 'dev',
        'type': 'GUIDE',
        'module': 'offline_mode',
        'version': '1.0',
    },

    # No frontmatter — add full frontmatter
    '131_REP_DEV_M0_EXECUTION_REPORT_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'M0',
        'version': '1.0',
    },
    '132_REP_DEV_M1_EXECUTION_REPORT_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'M1',
        'version': '1.0',
    },
    '133_REP_DEV_M2_EXECUTION_REPORT_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'M2',
        'version': '1.0',
    },
    '134_REP_DEV_M3_EXECUTION_REPORT_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'M3',
        'version': '1.0',
    },
    '135_REP_DEV_M4_EXECUTION_REPORT_1_0_DRAFT.md': {
        'status': 'IMPLEMENTED',
        'area': 'dev',
        'type': 'REP',
        'module': 'M4',
        'version': '1.0',
    },
    'diagrams/008_CLASS_DIAGRAM_RECPL_Chatgpt_1_0_DRAFT_.md': {
        'status': 'ACTIVE',
        'area': 'dev',
        'type': 'DIAGRAM',
        'module': 'RECPL',
        'version': '1.0',
    },
}

# Files with partial frontmatter (starts with --- but missing status/ closing)
# These need the status line injected
PARTIAL_FM_FILES = {
    '128_REP_DEV_PIPELINE_FIXES_VERIFICATION_1_0_DRAFT.md': 'IMPLEMENTED',
}


def has_frontmatter(content):
    return content.startswith('---')


def parse_frontmatter(content):
    """Find frontmatter boundaries. Returns (start, end) indices or None."""
    if not content.startswith('---'):
        return None
    end = content.find('---', 3)
    if end == -1:
        return None
    return (0, end + 3)


def update_status_in_frontmatter(content, new_status):
    """Replace the status: line in frontmatter."""
    result = re.sub(
        r'^status:\s*\S+',
        f'status: {new_status}',
        content,
        count=1,
        flags=re.MULTILINE
    )
    return result


def generate_frontmatter(meta):
    """Generate YAML frontmatter string."""
    lines = ['---']
    for key in ('id', 'area', 'type', 'module', 'version', 'status'):
        if key in meta:
            lines.append(f'{key}: {meta[key]}')
    if 'tags' in meta:
        lines.append(f'tags: {meta["tags"]}')
    if 'summary' in meta:
        lines.append(f'summary: {meta["summary"]}')
    if 'keywords' in meta:
        lines.append(f'keywords: {meta["keywords"]}')
    lines.append('---\n')
    return '\n'.join(lines)


def main():
    ok = 0
    err = 0
    skipped = 0
    added_frontmatter = 0

    # Process files with existing frontmatter
    for rel_path, new_status in sorted(MAPPING.items()):
        abs_path = os.path.join(DOCS_DIR, rel_path)
        if not os.path.exists(abs_path):
            print(f'  MISSING: {rel_path}')
            err += 1
            continue

        with open(abs_path, 'r') as f:
            content = f.read()

        if not has_frontmatter(content):
            print(f'  NO FM:   {rel_path} (needs frontmatter, expected status change to {new_status})')
            err += 1
            continue

        old_status_match = re.search(r'^status:\s*(\S+)', content, re.MULTILINE)
        old_status = old_status_match.group(1) if old_status_match else '?'
        new_content = update_status_in_frontmatter(content, new_status)
        if new_content == content:
            print(f'  UNCHANGED: {rel_path} (already {old_status})')
            skipped += 1
            continue

        with open(abs_path, 'w') as f:
            f.write(new_content)
        print(f'  {old_status:>12} -> {new_status:<12}  {rel_path}')
        ok += 1

    # Process files with partial frontmatter (missing status line)
    for rel_path, new_status in sorted(PARTIAL_FM_FILES.items()):
        abs_path = os.path.join(DOCS_DIR, rel_path)
        if not os.path.exists(abs_path):
            print(f'  MISSING: {rel_path}')
            err += 1
            continue

        with open(abs_path, 'r') as f:
            content = f.read()

        if not has_frontmatter(content):
            print(f'  NO FM:   {rel_path} (expected partial FM)')
            err += 1
            continue

        if re.search(r'^status:', content, re.MULTILINE):
            # Has status already, update it
            new_content = update_status_in_frontmatter(content, new_status)
        else:
            # No status line, inject after first --- or before area line
            # Find the second line (after the opening ---)
            lines = content.split('\n')
            # Find the first blank line or closing ---
            inject_pos = 1
            for i in range(1, len(lines)):
                if lines[i].strip() == '' or lines[i].strip() == '---':
                    inject_pos = i
                    break
            lines.insert(inject_pos, f'status: {new_status}')
            new_content = '\n'.join(lines)

        if new_content == content:
            print(f'  UNCHANGED: {rel_path}')
            skipped += 1
            continue

        with open(abs_path, 'w') as f:
            f.write(new_content)
        print(f'  {"(partial FM)":>12} -> {new_status:<12}  {rel_path}')
        ok += 1

    # Process files without frontmatter
    for rel_path, meta in sorted(FILES_WITHOUT_FRONTMATTER.items()):
        abs_path = os.path.join(DOCS_DIR, rel_path)
        if not os.path.exists(abs_path):
            print(f'  MISSING: {rel_path}')
            err += 1
            continue

        with open(abs_path, 'r') as f:
            content = f.read()

        if has_frontmatter(content):
            # Has frontmatter now, update status normally
            new_status = meta['status']
            old_status_match = re.search(r'^status:\s*(\S+)', content, re.MULTILINE)
            old_status = old_status_match.group(1) if old_status_match else '?'
            new_content = update_status_in_frontmatter(content, new_status)
            if new_content != content:
                with open(abs_path, 'w') as f:
                    f.write(new_content)
                print(f'  {old_status:>12} -> {new_status:<12}  {rel_path} (was no-FM, now updated)')
                ok += 1
            else:
                print(f'  UNCHANGED: {rel_path} (already {old_status})')
                skipped += 1
            continue

        # Build frontmatter
        fm = generate_frontmatter(meta)
        new_content = fm + content
        with open(abs_path, 'w') as f:
            f.write(new_content)
        print(f'  {"(none)":>12} -> {meta["status"]:<12}  {rel_path} (+ frontmatter)')
        added_frontmatter += 1
        ok += 1

    # Summary
    print(f'\n{"=" * 60}')
    print(f'  Total: {ok} updated, {skipped} skipped, {err} errors')
    print(f'  Frontmatter added: {added_frontmatter}')
    return 0 if err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
