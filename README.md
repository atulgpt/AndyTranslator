AndyTranslator
============
Python script that uses Google Translation service to localize Android strings and validate positional parameters for correctness

Table of Contents
* [Scripts](#scripts)
  * [gtranslate.py](#gtranslatepy)
  * [validate.py](#validatepy)

## Scripts

### gtranslate.py

This is a python module to automatically make string.xml file for different languages for Android

#### Setup
For using Google translation API, you have to [setup the Google translation api](https://cloud.google.com/translate/docs/setup) and then [download service account private key](https://cloud.google.com/translate/docs/setup#creating_service_accounts_and_keys) and export the variable to the path of the key at environment variable name `GOOGLE_APPLICATION_SERVICE_ACCOUNT_CREDENTIALS_FOR_TRANSLATION`

#### Arguments
This script has the following arguments:

* `-h`, `--help` show this help message and exit

* `-o`, `O` specify the absolute path of the output folder

* `-i`, `I` specify the absolute path of the input file
* `-lang`, `LANG` specify the comma-separated languages, ex: -lang 'en,it'
* `-f` force to redo the translation of all the key values, default = False
* `-p`, `POOL` set the number of process pool to use, default = 5
* `-v` enable the debug logs

#### Usage:
```bash
 python3 gtranslate.py [-h] [-o O] [-i I] [-lang LANG] [-f] [-p POOL] [-v]
```
e.g.
```bash
python3 gtranslate.py -i <input strings.xml path> -o <output folder where all values-<lang_code>/strings.xml will be upadated/created> -lang 'ar,de,es,fr,hi,it,ja,ko,pl,pt-rPT,ru,tl,vi,zh-rCN,zh-rTW' -v
```
In the output folder, you should have already copied `strings.xml` in `values-<lang_code>/strings.xml` so that only new keys will be translated.

### validate.py

This is a python module to verify the same number of **positional arguments**, **missing translation**, **warning characters(e.g., &, ..., -, --)** and **wrong xml escaping**

#### Arguments
This script has the following arguments:

* `-h`, `--help` show this help message and exit

* `-o`, `O` specify the absolute path of the output folder

* `-i`, `I` specify the absolute path of the input file
* `-lang`, `LANG` specify the comma-separated languages, ex: -lang 'en,it'
* `-p`, `POOL` set the number of process pool to use, default = 5
* `-v` enable the debug logs

#### Usage:
```bash
 python3 validate.py [-h] [-o O] [-i I] [-lang LANG] [-p POOL] [-v]
```
e.g.
```bash
python3 validate.py -i <input strings.xml path> -o <output folder where all values-<lang_code>/strings.xml will be upadated/created> -lang 'ar,de,es,fr,hi,it,ja,ko,pl,pt-rPT,ru,tl,vi,zh-rCN,zh-rTW' -v
```
