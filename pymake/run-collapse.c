/* Miscellaneous generic support functions for GNU Make.
Copyright (C) 1988-2020 Free Software Foundation, Inc.
This file is part of GNU Make.

GNU Make is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

GNU Make is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.  */

// Extract collapse_continuations() function from GNU Make 4.3
// Want to see how it works.
// davep 20230101
//
// gcc -g -Wall -Wpedantic -Wconversion -o run-collapse run-collapse.c
//

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

/*** copied from GNU Make 4.3 ***/

#  define ISBLANK(c) ((c) == ' ' || (c) == '\t')

int posix_pedantic = 0;

/* Discard each backslash-newline combination from LINE.
   Backslash-backslash-newline combinations become backslash-newlines.
   This is done by copying the text at LINE into itself.  */

void
collapse_continuations (char *line)
{
  char *out = line;
  char *in = line;
  char *q;

  q = strchr(in, '\n');
  if (q == 0)
    return;

  do
    {
      char *p = q;
      int i;
      size_t out_line_length;

      if (q > line && q[-1] == '\\')
        {
          /* Search for more backslashes.  */
          i = -2;
          while (&p[i] >= line && p[i] == '\\')
            --i;
          ++i;
        }
      else
        i = 0;

      /* The number of backslashes is now -I, keep half of them.  */
      out_line_length = (p - in) + i - i/2;
      if (out != in)
        memmove (out, in, out_line_length);
      out += out_line_length;

      /* When advancing IN, skip the newline too.  */
      in = q + 1;

      if (i & 1)
        {
          /* Backslash/newline handling:
             In traditional GNU make all trailing whitespace, consecutive
             backslash/newlines, and any leading non-newline whitespace on the
             next line is reduced to a single space.
             In POSIX, each backslash/newline and is replaced by a space.  */
          while (ISBLANK (*in))
            ++in;
          if (! posix_pedantic)
            while (out > line && ISBLANK (out[-1]))
              --out;
          *out++ = ' ';
        }
      else
        {
          /* If the newline isn't quoted, put it in the output.  */
          *out++ = '\n';
        }

      q = strchr(in, '\n');
    }
  while (q);

  memmove(out, in, strlen(in) + 1);
}

/*** end copied from GNU Make 4.3 ***/

/**
 *  Very nice hex dump function.
 *
 *  @author David Poole
 *  @version 1.0.0
 *  @param ptr
 *  @param size
 *
 */

void hex_dump( unsigned char *ptr, size_t size )
{
    static unsigned char hex_ascii[] =
       { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f' };
    int i;
    unsigned char line[80];
    unsigned char *ascii, *hex;
    unsigned char *endptr;
    size_t offset=0;

   endptr = ptr + size;
   memset( line, ' ', 80 );
   line[69] = 0;
   while( ptr != endptr ) {
      hex = &line[2];
      ascii = &line[52];
      for( i=0 ; i<16 ; i++ ) {
         if( isprint(*ptr) )
            *ascii++ = *ptr;
         else
            *ascii++ = '.';
         *hex++ = hex_ascii[ *ptr>>4 ];
         *hex++ = hex_ascii[ *ptr&0x0f ];
         *hex++ = ' ';
         ptr++;
         if( ptr == endptr ) {
            /* clean out whatever is left from the last line */
            memset( hex, ' ', (size_t)((15-i)*3) );
            memset( ascii, ' ', (size_t)(15-i) );
            break;
         }
      } printf( "0x%08lx %s\n", offset, line );
//      printf( "%d %p %p %s\n", i, ptr, ptr-i, line );
      offset += 16;
   }
}

void run(const char *src)
{
	char* s = strdup(src);

	collapse_continuations(s);
//    printf(">>%s<<\n\n", s);
	hex_dump((unsigned char *)s, strlen(s));
	free(s);
}

int main(void)
{
	run("space=\\\n\n");

	run("space=\\    \n");

	run("space=\\\nbar\n");

	// leading whitespace preserved
	run("   foo=\\\nbar\n");

	run("foo : bar ; baz\n");

	run("foo\\\nbar\\\nbaz\n");

	run("space=\\\n\\\n\\\n\n");

	run("foo\\\n:\\\nbar\\\n;\\\nbaz\n");

	run("   this  \\\n    is    \\\n   a\\\n  test   \\\n\n");

	run("   this  \\\n    is      a\\\n  test   \\\n\n");

	// from the GNU Make manual 3.1.1
	run("var:= one$\\\n   word\n");

	run("more-fun-in-assign\\\n=              \\\n   the    \\\n   leading   \\\n    and \\\n   trailing \\\n   white   \\\n     space     \\\n     should    \\\n    be    \\\n     eliminated \\\n   \\\n    \\\n   \\\n   including \\\n   \\\n    \\\n  blank  \\\n  \\\n   \\\n   lines\n");

	// literal backslash
	run("literal-backslash\\=foo\\ \n");

	// comments
	run("foo : # this comment\\\ncontinues on this line\n");

	run("foo\\\n\n");

	return 0;
}

