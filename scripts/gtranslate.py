#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This python script extracts string resources, calls Google translate
# and reassembles a new strings.xml as fitted for Android projects.

# Regex for format info for android studio string and number placeholder = (%(\d+\$)?s|(%(\d+\$)?d))

# LANGUAGE CODES FOR REFERENCE

#   af          Afrikaans
#   ak          Akan
#   sq          Albanian
#   am          Amharic
#   ar          Arabic
#   hy          Armenian
#   az          Azerbaijani
#   eu          Basque
#   be          Belarusian
#   bem         Bemba
#   bn          Bengali
#   bh          Bihari
#   xx-bork     Bork, bork, bork!
#   bs          Bosnian
#   br          Breton
#   bg          Bulgarian
#   km          Cambodian
#   ca          Catalan
#   chr         Cherokee
#   ny          Chichewa
#   zh-CN       Chinese (Simplified)
#   zh-TW       Chinese (Traditional)
#   co          Corsican
#   hr          Croatian
#   cs          Czech
#   da          Danish
#   nl          Dutch
#   xx-elmer    Elmer Fudd
#   en          English
#   eo          Esperanto
#   et          Estonian
#   ee          Ewe
#   fo          Faroese
#   tl          Filipino
#   fi          Finnish
#   fr          French
#   fy          Frisian
#   gaa         Ga
#   gl          Galician
#   ka          Georgian
#   de          German
#   el          Greek
#   gn          Guarani
#   gu          Gujarati
#   xx-hacker   Hacker
#   ht          Haitian Creole
#   ha          Hausa
#   haw         Hawaiian
#   iw          Hebrew
#   hi          Hindi
#   hu          Hungarian
#   is          Icelandic
#   ig          Igbo
#   id          Indonesian
#   ia          Interlingua
#   ga          Irish
#   it          Italian
#   ja          Japanese
#   jw          Javanese
#   kn          Kannada
#   kk          Kazakh
#   rw          Kinyarwanda
#   rn          Kirundi
#   xx-klingon  Klingon
#   kg          Kongo
#   ko          Korean
#   kri         Krio (Sierra Leone)
#   ku          Kurdish
#   ckb         Kurdish (Soranî)
#   ky          Kyrgyz
#   lo          Laothian
#   la          Latin
#   lv          Latvian
#   ln          Lingala
#   lt          Lithuanian
#   loz         Lozi
#   lg          Luganda
#   ach         Luo
#   mk          Macedonian
#   mg          Malagasy
#   ms          Malay
#   ml          Malayalam
#   mt          Maltese
#   mi          Maori
#   mr          Marathi
#   mfe         Mauritian Creole
#   mo          Moldavian
#   mn          Mongolian
#   sr-ME       Montenegrin
#   ne          Nepali
#   pcm         Nigerian Pidgin
#   nso         Northern Sotho
#   no          Norwegian
#   nn          Norwegian (Nynorsk)
#   oc          Occitan
#   or          Oriya
#   om          Oromo
#   ps          Pashto
#   fa          Persian
#   xx-pirate   Pirate
#   pl          Polish
#   pt-BR       Portuguese (Brazil)
#   pt-PT       Portuguese (Portugal)
#   pa          Punjabi
#   qu          Quechua
#   ro          Romanian
#   rm          Romansh
#   nyn         Runyakitara
#   ru          Russian
#   gd          Scots Gaelic
#   sr          Serbian
#   sh          Serbo-Croatian
#   st          Sesotho
#   tn          Setswana
#   crs         Seychellois Creole
#   sn          Shona
#   sd          Sindhi
#   si          Sinhalese
#   sk          Slovak
#   sl          Slovenian
#   so          Somali
#   es          Spanish
#   es-419      Spanish (Latin American)
#   su          Sundanese
#   sw          Swahili
#   sv          Swedish
#   tg          Tajik
#   ta          Tamil
#   tt          Tatar
#   te          Telugu
#   th          Thai
#   ti          Tigrinya
#   to          Tonga
#   lua         Tshiluba
#   tum         Tumbuka
#   tr          Turkish
#   tk          Turkmen
#   tw          Twi
#   ug          Uighur
#   uk          Ukrainian
#   ur          Urdu
#   uz          Uzbek
#   vi          Vietnamese
#   cy          Welsh
#   wo          Wolof
#   xh          Xhosa
#   yi          Yiddish
#   yo          Yoruba
#   zu          Zulu

#   RTL Languages

#   ar          Arabic
#   arc         Aramaic
#   az          Azeri
#   dv          Dhivehi/Maldivian
#   he          Hebrew
#   ku          Kurdish (Sorani)
#   per/fas     Persian/Farsi
#   ur          Urdu


#
#   SUBROUTINES
#

from multiprocessing import Pool
import shutil
import argparse
import re
from io import BytesIO
import sys
from lxml import etree as ET
import os
import requests
from fake_useragent import UserAgent
import html
import urllib.parse
import copy

debug = False


def log(msg):
    if debug:
        print(msg)

# This subroutine extracts the string including html tags
# and may replace "root[i].text".
# It cannot digest arbitrary encodings, so use it only if necessary.


def findall_content(xml_string, tag):
    pattern = r"<(?:\w+:)?%(tag)s(?:[^>]*)>(.*)</(?:\w+:)?%(tag)s" % {
        "tag": tag}
    return re.findall(pattern, xml_string, re.DOTALL)


def parse_response(r, text):
    # set markers that enclose the charset identifier

    if r is None:
        return text

    beforecharset = 'charset='
    aftercharset = '" http-equiv'
    # extract charset
    parsed1 = r.text[r.text.find(beforecharset)+len(beforecharset):]
    parsed2 = parsed1[:parsed1.find(aftercharset)]
    # Display warning when encoding mismatch
    if(parsed2 != r.encoding):
        print('\x1b[1;31;40m' + 'Warning: Potential Charset conflict')
        print(" Encoding as extracted by SELF    : "+parsed2)
        print(" Encoding as detected by REQUESTS : "+r.encoding + '\x1b[0m')
        raise ValueError

    # Work around an AGE OLD Python bug in case of windows-874 encoding
    # https://bugs.python.org/issue854511
    if(r.encoding == 'windows-874' and os.name == 'posix'):
        print('\x1b[1;31;40m' + "Alert: Working around age old Python bug (https://bugs.python.org/issue854511)\nOn Linux, charset windows-874 must be labeled as charset cp874"+'\x1b[0m')
        r.encoding = 'cp874'

    # convert html tags
    text = html.unescape(r.text)
    # set markers that enclose the wanted translation
    before_trans = 'class="t0">'
    after_trans = '</div><form'
    # extract translation and return it
    parsed1 = r.text[r.text.find(before_trans)+len(before_trans):]
    parsed2 = parsed1[:parsed1.find(after_trans)]
    # fix parameter strings
    parsed3 = re.sub('% ([ds])', r' %\1', parsed2)
    parsed4 = re.sub('% ([\d]) \$ ([ds])', r' %\1$\2', parsed3).strip()
    translated_string = html.unescape(parsed4).replace("'", r"\'")
    log(f"Translated string = {translated_string}")
    return translated_string


# This subroutine calls Google translate and extracts the translation from
# the html request
def translate(to_translate, to_language="auto", language="auto", name='no-name'):
    array_to_translate = []
    # print(to_translate)
    if '\\n' in to_translate:
        log(f'{name} contains \\n so splitting text')
        array_to_translate = to_translate.split('\\n')
    else:
        array_to_translate.append(to_translate)

    resp_array = []
    text_array = []
    for text in array_to_translate:
        print(f'text being translated(key = {name}) = {text}')
        if text.strip():
            # send request
            req_url = "https://translate.google.com/m?hl=%s&sl=%s&q=%s" % (
                to_language, language, urllib.parse.quote(text))
            log('\nrequest url = ' + req_url)

            # Making fake user-agent
            ua = UserAgent(use_cache_server=False,verify_ssl=False)
            userAgent = ua.random
            log(f'Randm userAgent = {userAgent}')
            headers = {"User-Agent": userAgent}
            cookies = {'GOOGLE_ABUSE_EXEMPTION': 'ID=196d8fb1efebf14e:TM=1601733587:C=r:IP=103.43.112.97-:S=APGng0vxwhbunwAPfP8XSWk9jHovjubUfQ'}
            resp_array.append(requests.get(req_url, headers=headers, cookies=cookies))
        else:
            print(f'Text is empty')
            resp_array.append(None)

        text_array.append(text)

    return '\\n'.join(map(parse_response, resp_array, text_array))


#
# MAIN PROGRAM
#

# import libraries


def make_folder(folder_name, overrite=False):
    if not os.path.exists(folder_name):
        print(f'Make folder {folder_name}')
        os.makedirs(folder_name)
        return True
    else:
        if overrite:
            print(f'Make folder already exist {folder_name}')
            shutil.rmtree(folder_name)
            os.makedirs(folder_name)
            return True
        else:
            return False


def print_element(initial_text, translated_text, name):
    log(f'[{name}] {initial_text} -> {translated_text}')


def translate_node(input_node, out_lang, in_lang, name):
    is_translatable = input_node.get('translatable') != 'false'

    # Translating the string tag
    if is_translatable:
        # Here you might want to replace root[i].text by the findall_content function
        # if you need to extract html tags
        # ~ totranslate="".join(findall_content(str(ET.tostring(root[i])),"string"))
        to_translate = input_node.text
        if(to_translate != None):
            try:
                translation_result = translate(
                    to_translate,
                    out_lang,
                    in_lang,
                    name
                )
                print_element(to_translate, translation_result, name)
                return translation_result
            except Exception as e:
                print(e)
                return None
        else:
            raise ValueError
    else:
        return None


def get_previous_string(root, id):
    if type(id) is not str:
        raise ValueError
    if root is None:
        return None
    answer_list = root.findall(f".//string[@name='{id}']")
    if len(answer_list) == 0:
        return None
    else:
        return answer_list[0].text


def get_previous_string_item(tag, root, id, index):
    if type(id) is not str:
        raise ValueError
    if root is None:
        return None
    answer_list = root.findall(f".//{tag}[@name='{id}']")
    if len(answer_list) == 0 or len(answer_list[0]) < index + 1:
        return None
    else:
        previous_item_text = answer_list[0][index].text
        if previous_item_text:
            return previous_item_text
        else:
            return None



def make_other_lang_string_file(in_lang, out_lang, in_file_path, out_folder_path, forced, debug_local):
    global debug
    debug = debug_local
    # create outfile name by appending the language code to the input file name
    # print('in_lang = {0}, out_lang = {1}, in_file_path = {2} and out_folder_path = {3}'.format(in_lang, out_lang, in_file_path, out_folder_path))
    name, ext = os.path.splitext(in_file_path)
    head, tail = os.path.split(in_file_path)
    out_file_path = os.path.join(out_folder_path, f'values-{out_lang}', tail)

    print(f'\n\nMaking values-{out_lang} folder at {out_file_path}')
    print(
        f'Making values-{out_lang} folder creation result = {make_folder(os.path.dirname(out_file_path))}')
    print('\n')

    # read xml structure
    print(f'Input string file name = {in_file_path}\n')
    parser = ET.XMLParser(remove_comments=False)
    input_tree = ET.parse(in_file_path)
    input_tree_root = input_tree.getroot()
    input_tree_working = copy.deepcopy(input_tree)
    input_tree_root_working = input_tree_working.getroot()

    # trying to read output xml if that exists
    if os.path.exists(out_file_path):
        log(f'File path values-{out_lang} does contain the strings.xml')
        output_tree = ET.parse(out_file_path)
        output_tree_root = output_tree.getroot()
    else:
        output_tree = None
        output_tree_root = None
        log(f'File path values-{out_lang} doesn\'t contain the strings.xml')

    # cycle through elements
    working_index = 0
    for i in range(len(input_tree_root)):
        # for each translatable string call the translation subroutine
        # and replace the string by its translation,
        # descend into each string array
        log('\n\n')

        input_node = input_tree_root[i]
        input_node_working = input_tree_root_working[working_index]

        # If comment then continue
        if not isinstance(input_node.tag, str):
            working_index = working_index + 1
            continue

        name_attr = input_node.attrib['name']
        print(f"{i} {input_node} and name = {name_attr}")
        # Translating the string tag
        if input_node.tag == 'string':
            log("processing string")

            if not input_node.text.startswith("@string/"):
                previous_translated_text = get_previous_string(
                    output_tree_root, name_attr)
                if previous_translated_text is None:
                    translated_result = translate_node(
                        input_node, out_lang, in_lang, name_attr)
                    if translated_result is not None:
                        input_node_working.text = translated_result
                    else:
                        input_tree_root_working.remove(input_node_working)
                        working_index = working_index - 1
                else:
                    input_node_working.text = previous_translated_text

        # Translating the string-array tag
        if(input_node.tag == 'string-array' or input_node.tag == "plurals"):
            log(f"processing {input_node.tag}")

            for j in range(len(input_node)):
                # for each translatable string call the translation subroutine
                # and replace the string by its translation,

                if(input_node[j].tag == 'item'):
                    if not input_node[j].text.startswith("@string/"):
                        previous_string = get_previous_string_item(
                            input_node.tag, output_tree_root, name_attr, j)
                        if previous_string is not None:
                            input_node_working[j].text = previous_string
                        else:
                            input_node_working[j].text = translate_node(
                                input_node[j], out_lang, in_lang, input_node.attrib['name'])
                else:
                    raise ValueError
        working_index = working_index + 1
        print('------------\n')

    # write new xml file
    print(f'Writing to fileName = {out_file_path}')
    input_tree_working.write(
        out_file_path, encoding='utf-8', xml_declaration=True)


def main(argv):
    global debug
    parser = argparse.ArgumentParser(
        description='This is a python module to automatically make string.xml file for different language for Android')
    parser.add_argument('-o', action="store", default='',
                        help='Specify the absolute path of output folder')
    parser.add_argument('-i', action="store",
                        help='Specify the absolute path of input file')
    parser.add_argument('-lang', action="store", default='',
                        help='Specify the comma seperated langauges, ex: -lang \'en,it\'')
    parser.add_argument('-f', action="store_true", default=False,
                        help='Force to redo the translation of all the key values, default = False')
    parser.add_argument('-p', action="store", dest='pool', default=5,
                        type=int, help='Number of process pool to use, default = 5')
    parser.add_argument('-v', action="store_true", dest='debug',
                        default=False, help='Enable the debug logs')

    args = parser.parse_args(argv)
    debug = args.debug

    print('\nScript run started:\n')
    log('\nDebug logs are enabled. Be prepared to bombarded by the terminal logs\n')
    print(f'Current script running path = {os.getcwd()}')

    if args.lang == '':
        print('No langauge specified exiting the program\n')
        parser.print_help(sys.stderr)
        sys.exit()

    if not os.path.exists(args.i):
        print(f'Input path({args.i}) doesn\'t exists so exiting the program\n')
        parser.print_help(sys.stderr)
        sys.exit()

    if os.path.isdir(args.i):
        print(f'Input path({args.i}) is directory so exiting the program\n')
        parser.print_help(sys.stderr)
        sys.exit()


    if not args.o.strip():
        args.o = os.path.join(os.path.dirname(args.i), 'output')
        make_folder(args.o)
        print(f'Output folder path not provided! Using output path = {args.o}')

    with Pool(args.pool) as p:
        array_lang = str(args.lang).split(',')
        array_lang_striped =  list(map(lambda it: it.strip(), array_lang))
        log(array_lang_striped)
        arg_map = map(lambda it: ('en', it, args.i,
                                  args.o, args.f, debug), array_lang_striped)
        p.starmap(make_other_lang_string_file, arg_map)


if __name__ == "__main__":
    main(sys.argv[1:])
    print('\nOn your right cap!')