PyVisca-3
=======

Fork of https://github.com/mutax/PyVisca. I had troubles using the 
original PyVisca from Python3, mainly for the way pyserial needs to 
handle bytes and byte arrays. I had major pains in many cases where
the original lib was using chr()/ord() to perform conversion.

I found that by switching entirely to a "bytes" python type 
representation my life was easier.

The camera reference in my case is SONY FCB-EV7500 and many commands
have been rewritten to work with this camera. 

In addition to command string, I have added implemented some nquiry 
strings to be able to read camera settings.

This is not a comprehensive implementation of ALL camera functionalities
but just of what was needed for my project, some commands may still be
missing.

Not Working
=======
Register setting seems not to be applied even after a power-off/on cycle
unless you physically switch the camera off/on.


