#!/usr/bin/python

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/142812

import logging
logger = logging.getLogger("hexdump")

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump(src, length=8):
    N=0; result=''
    while src:
       s,src = src[:length],src[length:]
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       s = s.translate(FILTER)
       result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
       N+=length
    return result

#def dump2(src, length=8):
#    result=[]
#    for i in xrange(0, len(src), length):
#       s = src[i:i+length]
#       hexa = ' '.join(["%02X"%ord(x) for x in s])
#       printable = s.translate(FILTER)
#       result.append("%04X   %-*s   %s\n" % (i, length*3, hexa, printable))
#    return ''.join(result)

def parse_hexdump( lines_list ) :

    # davep 01-Oct-2013 ; moving this function from calpy/pdparse.py into
    # hexdump.py. Seems to make more sense here.
    """Reverses a hexdump into an array of bytes. Parse a hexdump from an array
    of strings. Ignores lines that doesn't start with '0x'."""

    bytestr = ""

    for offset,line in enumerate(lines_list) : 
        
        line = line.strip()

        # skip junk lines
        if not line.startswith( "0x" ) :
            logger.warn( "line #{0} skip bad line \"{1}\"".format(offset,line) )
            continue

        fields = line.split( "   " )
#        print len(fields), fields

        hex_digits = fields[1].split()
        if len(hex_digits) != 16 :
            errmsg = "line #{0} invalid hexdump found \"{1}\"".format(offset,line)
            raise Exception( errmsg )

        bytestr += "".join([ chr(int(n,16)) for n in hex_digits ] )

    return bytestr

if __name__ == '__main__' :
    logging.basicConfig()

    logger.setLevel( level=logging.DEBUG )

    s=("This 10 line function is just a sample of python power "
       "for string manipulations.\n"
       "The code is \x07even\x08 quite readable!")

    logger.debug( dump(s, 16) )
#    print( dump2(s, 16 ) )

