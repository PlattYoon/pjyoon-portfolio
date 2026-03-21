15-122 Principles of Imperative Computation
Ropes

==========================================================

Files you won't modify:
   lib/hdict.o1      - Generic dictionaries using hashtables
                       (respect the interface!)

Files you will modify:
   rope.c1           - Interface of ropes
                       (you may optionally add new functions)
   rope-test.c0      - Test file with a main() function
                       (optional, highly recommended!)

==========================================================

Displaying the library interfaces
   % cc0 -i lib/hdict.o1

Compiling and running your code:
   % cc0 -d -W -o rope-test lib/*.o1 rope.c1 rope-test.c0
   % ./rope-test

==========================================================

Submitting from the command line on andrew:
   % autolab122 handin ropes rope.c1 rope-test.c0
or
   % autolab122 handin ropes rope.c1
then display autolab's feedback by running:
   % autolab122 feedback

Creating a tarball to submit with autolab.andrew.cmu.edu web interface:
   % tar -czvf handin.tgz rope.c1 rope-test.c0
or
   % tar -czvf handin.tgz rope.c1
