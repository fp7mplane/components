#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc,char *argv[])
{
    const char *msg = "killall tstat";
    setuid( 0 );
    system( msg );

    return 0;
}
