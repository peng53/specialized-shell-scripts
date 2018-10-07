
#!/bin/env python
import sys

if len(sys.argv)>=2:
	is_image = any(sys.argv[1].endswith(P) for P in ['.jpg','.jpeg','.png','.gif'])
	import os
	if (is_image):
		os.execv("/usr/bin/feh",sys.argv)
	else:
		os.execv("/usr/bin/dillo",sys.argv)
