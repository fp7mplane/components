#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc,char *argv[])
{
    char buf[256];
    if (argc != 5) 
    {
        printf("Wrong argument number for %s\n.", argv[0]);
        printf("Usage:\n %s tstat-path interface net-file outputdir", argv[0]);
        return 1;
    }
	
	//compile as root, chmod 4755, rename executable as start.out
    setuid( 0 );
    snprintf(buf, sizeof buf, "%s -i %s -l -u -E 1500 -N %s -s %s", argv[1], argv[2], argv[3], argv[4]);
    system( buf );

    return 0;
}
