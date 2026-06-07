The UNIX spell program does an adequate job of catching spelling errors in a document. For most 
people, however, it only does half the job. It doesn't help you correct the misspelled words. First-time 
users of spell find themselves jotting down the misspelled words and then using the text editor to 
change the document. More skilled users build a sed script to make the changes automatically.
The spellcheck program offers another way - it shows you each word that spell has found and 
asks if you want to correct the word. You can change each occurrence of the word after seeing the line 
on which it occurs, or you can correct the spelling error globally. You can also choose to add any word 
that spell turns up to a local dictionary file.
Before describing the program, let's have a demonstration of how it works. The user enters 
spellcheck, a shell script that invokes awk, and the name of the document file.
$ spellcheck ch00
Use local dict file? (y/n)y
If a dictionary file is not specified on the command line, and a file named dict exists in the current 
directory, then the user is asked if the local dictionary should be used. spellcheck then runs spell 
using the local dictionary.
Running spell checker ...
Using the list of "misspelled" words turned up by spell, spellcheck prompts the user to correct 
them. Before the first word is displayed, a list of responses is shown that describes what actions are 
possible.
Responses: 
        Change each occurrence, 
        Global change, 
        Add to Dict, 
        Help, 
        Quit 
        CR to ignore: 
1 - Found SparcStation (C/G/A/H/Q/):a
The first word found by spell is "SparcStation." A response of "a" (followed by a carriage return) 
adds this word to a list that will be used to update the dictionary. The second word is clearly a 
misspelling and a response of "g" is entered to make the change globally:
2 - Found languauge (C/G/A/H/Q/):g
Globally change to:language
Globally change languauge to language? (y/n):y
> and a full description of its scripting language. 
1 lines changed. Save changes? (y/n)y
After prompting the user to enter the correct spelling and confirming the entry, the change is made and 
each line affected is displayed, preceded by a ">". The user is then asked to approve these changes 
before they are saved. The third word is also added to the dictionary:
3 - Found nawk (C/G/A/H/Q/):a
The fourth word is a misspelling of "utilities." 
4 - Found utlitities (C/G/A/H/Q/):c
These utlitities have many things in common, including
      ^^^^^^^^^^
Change to:utilities
Change utlitities to utilities? (y/n):y
Two other utlitities that are found on the UNIX system
          ^^^^^^^^^^
Change utlitities to utilities? (y/n):y
>These utilities have many things in common, including
>Two other utilities that are found on the UNIX system
2 lines changed. Save changes? (y/n)y
The user enters "c" to change each occurrence. This response allows the user to see the line containing 
the misspelling and then make the change. After the user has made each change, the changed lines are 
displayed and the user is asked to confirm saving the changes.
It is unclear whether the fifth word is a misspelling or not, so the user enters "c" to view the line.
5 - Found xvf (C/G/A/H/Q/):c
tar xvf filename
    ^^^
Change to:RETURN
After determining that it is not a misspelling, the user enters a carriage return to ignore the word. 
Generally, spell turns up a lot of words that are not misspellings so a carriage return means to ignore 
the word.
After all the words in the list have been processed, or if the user quits before then, the user is prompted 
to save the changes made to the document and the dictionary.
Save corrections in ch00 (y/n)? y
Make changes to dictionary (y/n)? y
If the user answers "n," the original file and the dictionary are left unchanged.
Now let's look at the spellcheck.awk script, which can be divided into four sections:
The BEGIN procedure, that processes the command-line arguments and executes the spell 
command to create a word list.
The main procedure, that reads one word at a time from the list and prompts the user to make a 
correction.
The END procedure, that saves the working copy of the file, overwriting the original. It also 
appends words from the exception list to the current dictionary. 
Supporting functions, that are called to make changes in the file.
We will look at each of these sections of the program.
12.1.1 BEGIN Procedure
The BEGIN procedure for spellcheck.awk is large. It is also somewhat unusual.
# spellcheck.awk -- interactive spell checker
#
# AUTHOR: Dale Dougherty
#
# Usage: nawk -f spellcheck.awk [+dict] file 
# (Use spellcheck as name of shell program) 
# SPELLDICT = "dict" 
# SPELLFILE = "file"
# BEGIN actions perform the following tasks: 
#       1) process command-line arguments
#       2) create temporary filenames
#       3) execute spell program to create wordlist file
#       4) display list of user responses
BEGIN { 
# Process command-line arguments
# Must be at least two args -- nawk and filename
        if (ARGC > 1) {
        # if more than two args, second arg is dict 
                if (ARGC > 2) {
                # test to see if dict is specified with 
"+"  
files
it
                # and assign ARGV[1] to SPELLDICT
                        if (ARGV[1] ~ /^\+.*/) 
                                SPELLDICT = ARGV[1]
                        else 
                                SPELLDICT = "+" ARGV[1]
                # assign file ARGV[2] to SPELLFILE 
                        SPELLFILE = ARGV[2]
                # delete args so awk does not open them as 
                        delete ARGV[1]
                        delete ARGV[2]
                }
        # not more than two args
                else {
                # assign file ARGV[1] to SPELLFILE 
                        SPELLFILE = ARGV[1]
                # test to see if local dict file exists
                        if (! system ("test -r dict")) {
                        # if it does, ask if we should use 
                                printf ("Use local dict 
file? (y/n)")   
                                getline reply < "-"
                        # if reply is yes, use "dict" 
                                if (reply ~ /[yY](es)?/){
                                        SPELLDICT = "+dict"
                                }
                        }
                }
        } # end of processing args > 1 
        # if args not > 1, then print shell-command usage 
        else {
                print "Usage: spellcheck [+dict] file"
                exit 1
        }
# end of processing command line arguments
# create temporary file names, each begin with sp_
        wordlist = "sp_wordlist"
        spellsource = "sp_input"
        spellout = "sp_out"
# copy SPELLFILE to temporary input file
        system("cp " SPELLFILE " " spellsource)
# now run spell program; output sent to wordlist
        print "Running spell checker ..."
        if (SPELLDICT)
                SPELLCMD = "spell " SPELLDICT " "
        else
                SPELLCMD = "spell "
        system(SPELLCMD spellsource " > " wordlist )
# test wordlist to see if misspelled words turned up
        if ( system("test -s " wordlist ) ) {
        # if wordlist is empty (or spell command failed), 
exit
                print "No misspelled words found."
                system("rm " spellsource " " wordlist)
                exit
        }       
# assign wordlist file to ARGV[1] so that awk will read 
it.     
        ARGV[1] = wordlist
# display list of user responses 
        responseList = "Responses: \n\tChange each 
occurrence," 
        responseList = responseList "\n\tGlobal change," 
        responseList = responseList "\n\tAdd to Dict,"  
        responseList = responseList "\n\tHelp," 
        responseList = responseList "\n\tQuit" 
        responseList = responseList "\n\tCR to ignore: "
        printf("%s", responseList)
} # end of BEGIN procedure
The first part of the BEGIN procedure processes the command-line arguments. It checks that ARGC is 
greater than one for the program to continue. That is, in addition to "nawk," a filename must be 
specified. This file specifies the document that spell will analyze. An optional dictionary filename can 
be specified as the second argument. The spellcheck script follows the command-line interface of 
spell, although none of the obscure spell options can be invoked from the spellcheck command 
line. If a dictionary is not specified, then the script executes a test command to see if the file dict 
exists. If it does, the prompt asks the user to approve using it as the dictionary file.
Once we've processed the arguments, we delete them from the ARGV array. This is to prevent their being 
interpreted as filename arguments.
The second part of the BEGIN procedure sets up some temporary files, because we do not want to work 
directly with the original file. At the end of the program, the user will have the option of saving or 
discarding the work done in the temporary files. The temporary files all begin with "sp_" and are 
removed before exiting the program.
The third part of the procedure executes spell and creates a word list. We test to see that this file 
exists and that there is something in it before proceeding. If for some reason the spell program fails, 
or there are no misspelled words found, the wordlist file will be empty. If this file does exist, then we 
assign the filename as the second element in the ARGV array. This is an unusual but valid way of 
supplying the name of the input file that awk will process. Note that this file did not exist when awk was 
invoked! The name of the document file, which was specified on the command line, is no longer in the 
ARGV array. We will not read the document file using awk's main input loop. Instead, a while loop 
reads the file to find and correct misspelled words.
The last task in the BEGIN procedure is to define and display a list of responses that the user can enter 
when a misspelled word is displayed. This list is displayed once at the beginning of the program as well 
as when the user enters "Help" at the main prompt. Putting this list in a variable allows us to access it 
from different points in the program, if necessary, without maintaining duplicates. The assignment of 
responseList could be done more simply, but the long string would not be printable in this book. 
(You can't break a string over two lines.)
12.1.2 Main Procedure
The main procedure is rather small, merely displaying a misspelled word and prompting the user to enter 
an appropriate response. This procedure is executed for each misspelled word. 
One reason this procedure is short is because the central action - correcting a misspelled word - is 
handled by two larger user-defined functions, which we'll see in the last section.
# main procedure, executed for each line in wordlist.
#       Purpose is to show misspelled word and prompt user
#       for appropriate action.
{
# assign word to misspelling
        misspelling = $1 
        response = 1
        ++word
# print misspelling and prompt for response
        while (response !~ /(^[cCgGaAhHqQ])|^$/ ) {
                printf("\n%d - Found %s (C/G/A/H/Q/):", 
word, misspelling)
                getline response < "-"
        }
# now process the user's response
# CR - carriage return ignores current word 
# Help
        if (response ~ /[Hh](elp)?/) {
        # Display list of responses and prompt again.
                printf("%s", responseList)
                printf("\n%d - Found %s (C/G/A/Q/):", word, 
misspelling)
        }
# Quit
                getline response < "-"
        if (response ~ /[Qq](uit)?/) exit
# Add to dictionary
        if ( response ~ /[Aa](dd)?/) { 
                dict[++dictEntry] = misspelling
        }
# Change each occurrence
        if ( response ~ /[cC](hange)?/) {
        # read each line of the file we are correcting
                newspelling = ""; changes = ""
                while( (getline < spellsource) > 0){
                # call function to show line with 
misspelled word
                # and prompt user to make each correction 
                        make_change($0)
                # all lines go to temp output file
                        print > spellout
                }       
        # all lines have been read 
        # close temp input and temp output file
                close(spellout)
                close(spellsource)
        # if change was made
                if (changes){ 
                # show changed lines
                        for (j = 1; j <= changes; ++j)
                                print changedLines[j]
                        printf ("%d lines changed. ", 
changes) 
                # function to confirm before saving changes
                        confirm_changes()
                }
        }
# Globally change
        if ( response ~ /[gG](lobal)?/) {
        # call function to prompt for correction
        # and display each line that is changed.
        # Ask user to approve all changes before saving.
                make_global_change()
        }       
} # end of Main procedure
The first field of each input line from wordlist contains the misspelled word and it is assigned to 
misspelling. We construct a while loop inside which we display the misspelled word to the user 
and prompt for a response. Look closely at the regular expression that tests the value of response:
while (response !~ /(^[cCgGaAhHqQ])|^$/)
The user can only get out of this loop by entering any of the specified letters or by entering a carriage 
return - an empty line. The use of regular expressions for testing user input helps tremendously in 
writing a simple but flexible program. The user can enter a single letter "c" in lower- or uppercase or a 
word beginning with "c" such as "Change."
The rest of the main procedure consists of conditional statements that test for a specific response and 
perform a corresponding action. The first response is "help," which displays the list of responses again 
and then redisplays the prompt.
The next response is "quit." The action associated with quit is exit, which drops out of the main 
procedure and goes to the END procedure.
If the user enters "add," the misspelled word is put in the array dict and will be added as an exception 
in a local dictionary.
The "Change" and "Global" responses cause the program's real work to begin. It's important to 
understand how they differ. When the user enters "c" or "change," the first occurrence of the misspelled 
word in the document is displayed. Then the user is prompted to make the change. This happens for each 
occurrence in the document. When the user enters "g" or "global," the user is prompted to make the 
change right away, and all the changes are made at once without prompting the user to confirm each 
one. This work is largely handled by two functions, make_change() and make_global_change
(), which we'll look at in the last section. These are all the valid responses, except one. A carriage 
return means to ignore the misspelled word and get the next word in the list. This is the default action of 
the main input loop, so no conditional need be set up for it.
12.1.3 END Procedure
The END procedure, of course, is reached in one of the following circumstances:
The spell command failed or did not turn up any misspellings.
The list of misspelled words is exhausted.
The user has entered "quit" at a prompt.
The purpose of the END procedure is to allow the user to confirm any permanent change to the document 
or the dictionary.
# END procedure makes changes permanent.
# It overwrites the original file, and adds words
# to the dictionary.
# It also removes the temporary files.
END {
# if we got here after reading only one record, 
# no changes were made, so exit.
        if (NR <= 1) exit
# user must confirm saving corrections to file
        while (saveAnswer !~ /([yY](es)?)|([nN]o?)/ ) {
                printf "Save corrections in %s (y/n)? ", 
SPELLFILE
                getline saveAnswer < "-"
        }
# if answer is yes then mv temporary input file to SPELLFILE
# save old SPELLFILE, just in case
        if (saveAnswer ~ /^[yY]/) {
                system("cp " SPELLFILE " " SPELLFILE ".
orig")
                system("mv " spellsource " " SPELLFILE)
        }
# if answer is no then rm temporary input file
        if (saveAnswer ~ /^[nN]/)
                system("rm " spellsource) 
# if words have been added to dictionary array, then prompt
# to confirm saving in current dictionary. 
        if (dictEntry) {
                printf "Make changes to dictionary (y/n)? "
                getline response < "-"
                if (response ~ /^[yY]/){
                # if no dictionary defined, then use "dict"
                        if (! SPELLDICT) SPELLDICT = "dict"
                # loop through array and append words to 
dictionary
SPELLDICT
tmp_dict")
        }
# remove word list
                        sub(/^\+/, "", SPELLDICT)
                        for ( item in dict )
                                print dict[item] >> 
                        close(SPELLDICT)
                # sort dictionary file 
                        system("sort " SPELLDICT "> 
                        system("mv " "tmp_dict " SPELLDICT)
                }
        system("rm sp_wordlist")
} # end of END procedure
The END procedure begins with a conditional statement that tests that the number of records is less than 
or equal to 1. This occurs when the spell program does not generate a word list or when the user 
enters "quit" after seeing just the first record. If so, the END procedure is exited as there is no work to 
save.
Next, we create a while loop to ask the user about saving the changes made to the document. It 
requires the user to respond "y" or "n" to the prompt. If the answer is "y," the temporary input file 
replaces the original document file. If the answer is "n," the temporary file is removed. No other 
responses are accepted.
Next, we test to see if the dict array has something in it. Its elements are the words to be added to the 
dictionary. If the user approves adding them to the dictionary, these words are appended to the current 
dictionary, as defined above, or if not, to a local dict file. Because the dictionary must be sorted to be 
read by spell, a sort command is executed with the output sent to a temporary file that is afterwards 
copied over the original file.
12.1.4 Supporting Functions
There are three supporting functions, two of which are large and do the bulk of the work of making 
changes in the document. The third function supports that work by confirming that the user wants to 
save the changes that were made.
When the user wants to "Change each occurrence" in the document, the main procedure has a while 
loop that reads the document one line at a time. (This line becomes $0.) It calls the make_change() 
function to see if the line contains the misspelled word. If it does, the line is displayed and the user is 
prompted to enter the correct spelling of the word.
# make_change -- prompt user to correct misspelling 
#                for current input line.  Calls itself
#                to find other occurrences in string.
#       stringToChange -- initially $0; then unmatched 
substring of $0
#       len -- length from beginning of $0 to end of 
matched string 
# Assumes that misspelling is defined. 
function make_change (stringToChange, len,      # parameters
        line, OKmakechange, printstring, carets)        # 
locals
{
# match misspelling in stringToChange; otherwise do nothing 
  if ( match(stringToChange, misspelling) ) {
  # Display matched line 
        printstring = $0
        gsub(/\t/, " ", printstring)
        print printstring
        carets = "^"
        for (i = 1; i < RLENGTH; ++i)
                carets = carets "^"
        if (len)
                FMT = "%" len+RSTART+RLENGTH-2 "s\n"
        else
                FMT = "%" RSTART+RLENGTH-1 "s\n"
        printf(FMT, carets)
  # Prompt user for correction, if not already defined
        if (! newspelling) {
                printf "Change to:"
                getline newspelling < "-"
        }
  # A carriage return falls through
  # If user enters correction, confirm  
        while (newspelling && ! OKmakechange) {
                printf ("Change %s to %s? (y/n):", 
misspelling, newspelling)
                getline OKmakechange < "-"
                madechg = ""
        # test response
                if (OKmakechange ~ /[yY](es)?/ ) {
                # make change (first occurrence only)
                        madechg = sub(misspelling, 
newspelling, stringToChange)
                }
                else if ( OKmakechange ~ /[nN]o?/ ) {
                        # offer chance to re-enter 
correction 
                        printf "Change to:"
                        getline newspelling < "-"
                        OKmakechange = ""
                }
        } # end of while loop
   # if len, we are working with substring of $0
        if (len) {
        # assemble it
                line = substr($0,1,len-1)
                $0 = line stringToChange
        }
        else {
        }
                $0 = stringToChange
                if (madechg) ++changes
   # put changed line in array for display
        if (madechg) 
                changedLines[changes] = ">" $0
   # create substring so we can try to match other 
occurrences
        len += RSTART + RLENGTH
        part1 = substr($0, 1, len-1)
        part2 = substr($0, len)
   # calls itself to see if misspelling is found in 
remaining part 
        make_change(part2, len) 
  } # end of if
} # end of make_change()
If the misspelled word is not found in the current input line, nothing is done. If it is found, this function 
shows the line containing the misspelling and asks the user if it should be corrected. Underneath the 
display of the current line is a row of carets that indicates the misspelled word.
Two other utlitities that are found on the UNIX system
          ^^^^^^^^^^
The current input line is copied to printstring because it is necessary to change the line for display 
purposes. If the line contains any tabs, each tab in this copy of the line is temporarily replaced by a 
single space. This solves a problem of aligning the carets when tabs were present. (A tab counts as a 
single character when determining the length of a line but actually occupies greater space when 
displayed, usually five to eight characters long.)
After displaying the line, the function prompts the user to enter a correction. It then follows up by 
displaying what the user has entered and asks for confirmation. If the correction is approved, the sub() 
function is called to make the change. If not approved, the user is given another chance to enter the 
correct word.
Remember that the sub() function only changes the first occurrence on a line. The gsub() function 
changes all occurrences on a line, but we want to allow the user to confirm each change. Therefore, we 
have to try to match the misspelled word against the remaining part of the line. And we have to be able 
to match the next occurrence regardless of whether or not the first occurrence was changed.
To do this, make_change() is designed as a recursive function; it calls itself to look for additional 
occurrences on the same line. In other words, the first time make_change() is called, it looks at all of 
$0 and matches the first misspelled word on that line. Then it splits the line into two parts - the first part 
contains the characters up to the end of the first occurrence and the second part contains the characters 
that immediately follow up to the end of the line. Then it calls itself to try and match the misspelled 
word in the second part. When called recursively, the function takes two arguments.
make_change(part2, len)
The first is the string to be changed, which is initially $0 when called from the main procedure but each 
time thereafter is the remaining part of $0. The second argument is len or the length of the first part, 
which we use to extract the substring and reassemble the two parts at the end.
The make_change() function also collects an array of lines that were changed.
# put changed line in array for display
        if (madechg)
                changedLines[changes] = ">" $0
The variable madechg will have a value if the sub() function was successful. $0 (the two parts have 
been rejoined) is assigned to an element of the array. When all of the lines of the document have been 
read, the main procedure loops through this array to display all the changed lines. Then it calls the 
confirm_changes() function to ask if these changes should be saved. It copies the temporary 
output file over the temporary input file, keeping intact the corrections made for the current misspelled 
word.
If a user decides to make a "Global change," the make_global_change() function is called to do it. 
This function is similar to the make_change() function, but is simpler because we can make the 
change globally on each line.
# make_global_change -
#               prompt user to correct misspelling 
#               for all lines globally.  
#               Has no arguments
# Assumes that misspelling is defined. 
function make_global_change(    newspelling, OKmakechange, 
changes)
{
# prompt user to correct misspelled word
   printf "Globally change to:"
   getline newspelling < "-"
# carriage return falls through
# if there is an answer, confirm 
   while (newspelling && ! OKmakechange) {
                printf ("Globally change %s to %s? (y/n):", 
misspelling,
                                newspelling)
                getline OKmakechange < "-"
        # test response and make change
                if (OKmakechange ~ /[yY](es)?/ ) {
                # open file, read all lines 
using gsub
                        while( (getline < spellsource) > 0){
                        # if match is found, make change 
                        # and print each changed line.
                                if ($0 ~ misspelling) {
                                        madechg = gsub
(misspelling, newspelling)
                                        print ">", $0
                                        changes += 1  # 
counter for line changes
                                }
                        # write all lines to temp output 
file
                                print > spellout
                        } # end of while loop for reading 
file
                # close temporary files
                        close(spellout)
                        close(spellsource)
                # report the number of changes  
                        printf ("%d lines changed. ", 
changes) 
                # function to confirm before saving changes
                        confirm_changes()
                } # end of if (OKmakechange ~ y) 
        # if correction not confirmed,  prompt for new word
                else if ( OKmakechange ~ /[nN]o?/ ){
                        printf "Globally change to:"
                        getline newspelling < "-"
                        OKmakechange = ""
                }
  } # end of while loop for prompting user for correction
} # end of make_global_change()
This function prompts the user to enter a correction. A while loop is set up to read all the lines of the 
document and apply the gsub() function to make the changes. The main difference is that all the 
changes are made at once - the user is not prompted to confirm them. When all lines have been read, the 
function displays the lines that were changed and calls confirm_changes() to get the user to 
approve this batch of changes before saving them.
The confirm_changes() function is a routine called to get approval of the changes made when the 
make_change() or make_global_change() function is called.
# confirm_changes --  
#               confirm before saving changes
function confirm_changes(  savechanges) {
# prompt to confirm saving changes
        while (! savechanges ) {
                printf ("Save changes? (y/n)")
                getline savechanges < "-"
        }
# if confirmed, mv output to input
        if (savechanges ~ /[yY](es)?/)
                system("mv " spellout " " spellsource) 
}
The reason for creating this function is to prevent the duplication of code. Its purpose is simply to 
require the user to acknowledge the changes before replacing the old version of the document file 
(spellsource) with the new version (spellout).
12.1.5 The spellcheck Shell Script
To make it easy to invoke this awk script, we create the spellcheck shell script (say that three times 
fast). It contains the following lines:
AWKLIB=/usr/local/awklib
nawk -f $AWKLIB/spellcheck.awk $*
This script sets up a shell variable AWKLIB that specifies the location of the spellcheck.awk script. 
The symbol "$*" expands to all command-line parameters following the name of the script. These 
parameters are then available to awk.
One of the interesting things about this spell checker is how little is done in the shell script.[1] All of the 
work is done in the awk programming language, including executing 10 UNIX commands. We're using 
a consistent syntax and the same constructs by doing it all in awk. When you have to do some of your 
work in the shell and some in awk, it can get confusing. For instance, you have to remember the 
differences in the syntax of if conditionals and how to reference variables. Modern versions of awk 
provide a true alternative to the shell for executing commands and interacting with a user. The full 
listing for spellcheck.awk is found in Appendix C, Supplement for Chapter 12.
[1] UNIX Text Processing (Dougherty and O'Reilly, Howard W. Sams, 1987) presents a 
sed-based spell checker that relies heavily upon the shell. It is interesting to compare the 
