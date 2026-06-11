Adobe FrameMaker is a document processor designed for writing and editing large or complex documents, including structured documents. It was originally developed by Frame Technology Corporation, which was bought by Adobe.

Overview
FrameMaker became an Adobe product in October 1995 when Adobe purchased Frame Technology Corp.[4] Adobe added SGML support, which was eventually adapted into XML support. In April 2004, Adobe stopped supporting FrameMaker for the Macintosh.[5]

This reinvigorated rumors surfacing in 2001 that product development and support for FrameMaker were being wound down. Adobe denied these rumors in 2001,[6] later releasing FrameMaker 8 at the end of July 2007, FrameMaker 9 in 2009, FrameMaker 10 in 2011, FrameMaker 11 in 2012, FrameMaker 12 in 2014, FrameMaker (2015 release - confusingly, internal version 13.0) in June 2015, FrameMaker 2017 (internal version 14.0) in January 2017, FrameMaker 2019 (internal version 15.0) in August 2018, FrameMaker 2020 (internal version 16.0) in 2020, and FrameMaker 2022 (internal version 17.0) in 2022.

FrameMaker has two ways of approaching documents: structured and unstructured.

Structured FrameMaker is used to achieve consistency in documentation within industries such as aerospace, where several models of the same complex product exist, or pharmaceuticals, where translation and standardization are important requirements in communications about products. Structured FrameMaker uses SGML and XML concepts. The author works with an EDD (Element Definition Document), which is a FrameMaker-specific DTD (Document Type Definition). The EDD defines the structure of a document where meaningful units are designated as elements nested in each other depending on their relationships, and where the formatting of these elements is based on their contexts. Attributes or Metadata can be added to these elements and used for single source publishing or for filtering elements during the output processes (such as publishing for print or for Web-based display). The author can view the conditions and contexts in a tree-like structure derived from the grammar (as specified by the DTD) or as formatted in a typical final output form.
Unstructured FrameMaker uses tagged paragraphs without any imposed logical structure, except that expressed by the author’s concept, topic organization, and the formatting supplied by paragraph and character tags.
When a user opens a structured file in unstructured FrameMaker, the structure is lost.

MIF
MIF (Maker Interchange Format) is a markup language that functions as a companion to FrameMaker. MIF always had 3 purposes. The first was to represent FrameMaker documents in a relatively simple ASCII-based format, which can be produced or understood by other software systems and also by human operators. The second was to ensure any version of FrameMaker could read a document produced by any other version, at least to the extent it had the same features. While every version of FrameMaker could read the last couple of version's documents, reading them all took too much software effort and testing, so reading MIF was sufficient. The third was to ensure that FrameMaker would never lose a writer's work. If FrameMaker crashed, it would first write out the current document in MIF.

Any document that can be created interactively in FrameMaker can also be represented, exactly and completely, in MIF (the reverse, however, is not true: a few FrameMaker features are available only through MIF). All versions of FrameMaker can export documents in MIF, and can also read MIF documents, including documents created by an earlier version or by another program.

History
icon
This section needs additional citations for verification. Please help improve this article by adding citations to reliable sources in this section. Unsourced material may be challenged and removed. (April 2013) (Learn how and when to remove this message)
Frame Technology was founded in 1986 by David Murray, Charles Corfield, Steven Kirsch, and Vickie Blackslee. [7]

While working on his doctorate in astrophysics at Columbia University, Corfield, a mathematician alumnus of the St John's College, Cambridge, decided to write a WYSIWYG document editor on a Sun-2 workstation.

The only substantial DTP product at the time of FrameMaker's conception was Interleaf, which also ran on Sun workstations.[8]

After only a few months, Corfield had completed a functional prototype he called /etc/publisher. The prototype caught the eye of salesmen at the fledgling Sun Microsystems, which lacked commercial applications to showcase the graphics capabilities of their workstations. They got permission from Corfield to use the prototype of /etc/publisher as demoware for their computers.

Kirsch and Blakeslee were founding members of Mouse Systems, where they brought on Murray as Director of Application Software Development. In early 1986, Kirsch and Murray were visiting Sun Microsystems where they were given a demonstration of /etc/publisher. They thought there was a great opportunity for this and contacted Corfield. After several days of meetings they decided to form a company together. Kirsch, Murray, and Blakeslee left Mouse Systems and Corfield moved from New York to join them.[9]

Originally written for SunOS (a variant of UNIX) on Sun machines, FrameMaker was a popular technical writing tool, and the company was profitable early on. Because of the flourishing desktop publishing market on the Apple Macintosh, the software was ported to the Mac as its second platform.

In the early 1990s, a wave of UNIX workstation vendors—Apollo, Data General, MIPS, Motorola and Sony—provided funding to Frame Technology for an OEM version for their platforms.

At the height of its success, FrameMaker ran on more than thirteen UNIX platforms, including NeXT Computer's NeXTSTEP, Dell's System V Release 4 UNIX and IBM's AIX operating systems.

Sun Microsystems and AT&T were promoting the OPEN LOOK GUI standard to win over Motif, so Sun contracted Frame Technology to implement a version of FrameMaker on their PostScript-based NeWS windowing system. The NeWS version of FrameMaker was successfully released to those customers adopting the OPEN LOOK standards.

FrameMaker enabled authors to produce highly structured documents with a great deal of typographical control in a WYSIWYG way.

Frame Technology later ported FrameMaker to Microsoft Windows, but the company lost direction soon after its release. Up to this point, FrameMaker had been targeting a professional market for highly technical publications, such as the maintenance manuals for the Boeing 777 project, and licensed each copy for $2,500. But the Windows version brought the product to the $500 price range, which cannibalized its own non-Windows customer base.

The company's attempt to sell sophisticated technical publishing software to the home DTP market was a disaster. A tool designed for a 1,000-page manual was too cumbersome and difficult for an average home user to type a one-page letter.

Adobe Systems acquired the product and returned the focus to the professional market. Then, they released a new version under the name Adobe FrameMaker 5.1 in 1996. Today, Adobe FrameMaker is still a widely used publication tool for technical writers, although no version has been released for the Mac OS X operating system, limiting use of the product. The decision to cancel FrameMaker for OS X caused considerable friction between Adobe and Mac users, including Apple itself, which relied on it for creating documentation. As late as 2008, Apple manuals for OS X Leopard[10] and the iPhone[11] were still being developed on FrameMaker 7 in Classic mode; Apple has since switched to using InDesign.

FrameMaker versions 5.x through 7.2 (from mid-1995 to 2005) did not contain updates to major parts of the program (including its general user interface, table editing, and illustration editing), concentrating instead on bug fixes and the integration of XML-oriented features (previously part of the FrameMaker+SGML premium product). FrameMaker did not feature multiple undo until version 7.2 (its 2005 release).

FrameMaker 8 (2007) introduced Unicode, Flash, 3D, and built-in DITA support. Platform support included Windows (2000, XP, and Vista) and Sun Solaris (8, 9, and 10).

FrameMaker 9 (2009) introduced a redesigned user interface and several enhancements, including: full support for DITA, support for more media types, better PDF output, and enhanced WebDAV-based CMS integration. Platform support for Sun Solaris and Windows 2000 was dropped, leaving Windows XP and Windows Vista as the sole remaining platforms.

FrameMaker 10 (2011) again refined the user interface and introduced several changes, including: integration with content management systems via EMC Documentum 6.5 with Service Pack 1 and Microsoft SharePoint Server 2007 with Service Pack 2.

Other FrameMaker tools
FrameMaker Publishing Server is an online document processor server for automated creation of multi-use content types. The web interface enables users to direct aggregation of differing information sources routinely into detailed a presentation in multiple environments on numerous devices.[12]
Alternatives and competition
There were several major competitors in the technical publishing market, such as Arbortext, Interleaf, and Corel Ventura. Many academic users now use LaTeX,[13] because modern editors have made that system increasingly user-friendly, and LyX allows LaTeX to be generated with little or no knowledge of LaTeX. Several formats, including DocBook XML, target authors of technical documents about computer hardware and software. Lastly, alternatives to FrameMaker for technical writing include Help authoring tools and XML editors.