---
id: 001
area: legacy
type: guide
module: masterindex
version: 1.0
status: OBSOLETE
tags:
  - legacy
  - reference
  - masterindex
  - indexing
  - troff
  - dougherty
summary: "Documentacion original del programa masterindex por Dale Dougherty. Programa de indexacion para indices de un solo volumen y multivolumen. Codigo de referencia para el proyecto."
keywords:
  - masterindex
  - indexing
  - troff
  - reference
  - legacy
  - dougherty
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Frontmatter YAML agregado
---

C.3 Documentation for masterindex
This documentation, and the notes that follow, are by Dale Dougherty.
C.3.1 masterindex
indexing program for single and multivolume indexing.
Synopsis
masterindex [-master [volume]] [-page] [-screen] 
[filename..]
Description
masterindex generates a formatted index based on structured index entries output by 
troff. Unless you redirect output, it comes to the screen. 
Options-m or -master indicates that you are compiling a multivolume index. The index entries for 
each volume should be in a single file and the filenames should be listed in sequence. If 
the first file is not the first volume, then specify the volume number as a separate 
argument. The volume number is converted to a roman numeral and prepended to all the 
page numbers of entries in that file.-p or -page produces a listing of index entries for each page number. It can be used to 
proof the entries against hardcopy.-s or -screen specifies that the unformatted index will be viewed on the "screen". The 
default is to prepare output that contains troff macros for formatting.
Files
/work/bin/masterindex
/work/bin/page.idx
/work/bin/pagenums.idx
/work/bin/combine.idx
/work/bin/format.idx
/work/bin/rotate.idx
/work/bin/romanum
/work/macros/current/indexmacs
See Also
Note that these programs require "nawk" (new awk): nawk (1), and sed (1V).
Bugs
The new index program is modular, invoking a series of smaller programs. This should 
allow me to connect different modules to implement new features as well as isolate and 
fix problems more easily. Index entries should not contain any troff font changes. The 
program does not handle them. Roman numerals greater than eight will not be sorted 
properly, thus imposing a limit of an eight-book index. (The sort program will sort the 
roman numerals 1-10 in the following order: I, II, III, IV, IX, V, VI, VII, VIII, X.)
C.3.2 Background Details
Tim O'Reilly recommends The Joy of Cooking (JofC) index as an ideal index. I examined the JofC index 
quite thoroughly and set out to write a new indexing program that duplicated its features. I did not 
wholly duplicate the JofC format, but this could be done fairly easily if desired. Please look at the JofC 
index yourself to examine its features.
I also tried to do a few other things to improve on the previous index program and provide more support 
for the person coding the index.
C.3.3 Coding Index Entries
This section describes the coding of index entries in the document file. We use the .XX macro for 
placing index entries in a file. The simplest case is:
.XX "entry"
If the entry consists of primary and secondary sort keys, then we can code it as:
.XX "primary, secondary"
A comma delimits the two keys. We also have a .XN macro for generating "See" references without a 
page number. It is specified as:
.XN "entry (See anotherEntry)"
While these coding forms continue to work as they have, masterindex provides greater flexibility by 
allowing three levels of keys: primary, secondary, and tertiary. You'd specify the entry like so:
.XX "primary: secondary; tertiary"
Note that the comma is not used as a delimiter. A colon delimits the primary and secondary entry; the 
semicolon delimits the secondary and tertiary entry. This means that commas can be a part of a key 
using this syntax. Don't worry, though, you can continue to use a comma to delimit the primary and 
secondary keys. (Be aware that the first comma in a line is converted to a colon, if no colon delimiter is 
found.) I'd recommend that new books be coded using the above syntax, even if you are only specifying 
a primary and secondary key.
Another feature is automatic rotation of primary and secondary keys if a tilde (~) is used as the 
delimiter. So the following entry:
.XX "cat~command"
is equivalent to the following two entries:
.XX "cat command"
.XX "command: cat"
You can think of the secondary key as a classification (command, attribute, function, etc.) of the primary 
entry. Be careful not to reverse the two, as "command cat" does not make much sense. To use a tilde in 
an entry, enter "~~".
I added a new macro, .XB, that is the same as .XX except that the page number for this index entry will 
be output in bold to indicate that it is the most significant page number in a range. Here is an example:
.XB "cat command"
When troff processes the index entries, it outputs the page number followed by an asterisk. This is 
how it appears when output is seen in screen format. When coded for troff formatting, the page 
number is surrounded by the bold font change escape sequences. (By the way, in the JofC index, I 
noticed that they allowed having the same page number in roman and in bold.) Also, this page number 
will not be combined in a range of consecutive numbers.
One other feature of the JofC index is that the very first secondary key appears on the same line with the 
primary key. The old index program placed any secondary key on the next line. The one advantage of 
doing it the JofC way is that entries containing only one secondary key will be output on the same line 
and look much better. Thus, you'd have "line justification, definition of" rather than having "definition 
of" indented on the next line. The next secondary key would be indented. Note that if the primary key 
exists as a separate entry (it has page numbers associated with it), the page references for the primary 
key will be output on the same line and the first secondary entry will be output on the next line.
To reiterate, while the syntax of the three-level entries is different, this index entry is perfectly valid:
.XX "line justification, definition of"
It also produces the same result as:
.XX "line justification: definition of"
(The colon disappears in the output.) Similarly, you could write an entry, such as
.XX "justification, lines, defined"
or
.XX "justification: lines, defined"
where the comma between "lines" and "defined" does not serve as a delimiter but is part of the 
secondary key.
The previous example could be written as an entry with three levels:
.XX "justification: lines; defined"
where the semicolon delimits the tertiary key. The semicolon is output with the key, and multiple 
tertiary keys may follow immediately after the secondary key.
The main thing, though, is that page numbers are collected for all primary, secondary, and tertiary keys. 
Thus, you could have output such as:
  justification  4-9
    lines 4,6; defined, 5
C.3.4 Output Format
One thing I wanted to do that our previous program did not do is generate an index without the troff 
codes. masterindex has three output modes: troff, screen, and page.
The default output is intended for processing by troff (via fmt). It contains macros that are defined 
in /work/macros/current/indexmacs. These macros should produce the same index format as before, 
which was largely done directly through troff requests. Here are a few lines off the top:
$ masterindex ch01
.so /work/macros/current/indexmacs
.Se "" "Index"
.XC
.XF A "A"
.XF 1 "applications, structure of  2;  program  1"
.XF 1 "attribute, WIN_CONSUME_KBD_EVENTS  13"
.XF 2 "WIN_CONSUME_PICK_EVENTS  13"
.XF 2 "WIN_NOTIFY_EVENT_PROC  13"
.XF 2 "XV_ERROR_PROC  14"
.XF 2 "XV_INIT_ARGC_PTR_ARGV  5,6"
The top two lines should be obvious. The .XC macro produces multicolumn output. (It will print out two 
columns for smaller books. It's not smart enough to take arguments specifying the width of columns, but 
that should be done.) The .XF macro has three possible values for its first argument. An "A" indicates 
that the second argument is a letter of the alphabet that should be output as a divider. A "1" indicates that 
the second argument contains a primary entry. A "2" indicates that the entry begins with a secondary 
entry, which is indented.
When invoked with the -s argument, the program prepares the index for viewing on the screen (or 
printing as an ASCII file). Again, here are a few lines:
$ masterindex -s ch01
                A
applications, structure of  2;  program  1
attribute, WIN_CONSUME_KBD_EVENTS  13
  WIN_CONSUME_PICK_EVENTS  13
  WIN_NOTIFY_EVENT_PROC  13
  XV_ERROR_PROC  14
  XV_INIT_ARGC_PTR_ARGV  5,6
  XV_INIT_ARGS  6
  XV_USAGE_PROC  6
Obviously, this is useful for quickly proofing the index. The third type of format is also used for 
proofing the index. Invoked using -p, it provides a page-by-page listing of the index entries.
$ masterindex -p ch01
Page 1
        structure of XView applications
        applications, structure of; program
        XView applications
        XView applications, structure of
        XView interface
        compiling XView programs
        XView, compiling programs
Page 2
        XView libraries
C.3.5 Compiling a Master Index
A multivolume master index is invoked by specifying the -m option. Each set of index entries for a 
particular volume must be placed in a separate file.
$ masterindex -m -s book1 book2 book3
xv_init() procedure  II: 4; III: 5
XV_INIT_ARGC_PTR_ARGV attribute  II: 5,6
XV_INIT_ARGS attribute  I: 6
Files must be specified in consecutive order. If the first file is not Volume 1, you can specify the number 
as an argument.
$ masterindex -m 4 -s book4 book5 