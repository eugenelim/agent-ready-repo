# Intentionally-poisonous filename

This file's name, `CON`, is a reserved device name on Windows. A pack
that ships this file cannot be installed on a native-Windows adopter
machine; the lint catches it before release.
