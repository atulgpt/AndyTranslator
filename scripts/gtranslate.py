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
import sys
import traceback
from lxml import etree as ET
import os
import requests
import html
import urllib.parse
import copy
import six
import core.fileutils as string_fileutils

# install google-cloud-translate
from google.cloud import translate_v2 as google_translate_sdk

debug = False


def log(msg):
    if debug:
        print(msg)


# This subroutine extracts the string including html tags
# and may replace "root[i].text".
# It cannot digest arbitrary encodings, so use it only if necessary.


def findall_content(xml_string, tag):
    pattern = r"<(?:\w+:)?%(tag)s(?:[^>]*)>(.*)</(?:\w+:)?%(tag)s" % {"tag": tag}
    return re.findall(pattern, xml_string, re.DOTALL)


def parse_response(r, text):
    # set markers that enclose the charset identifier

    if r is None:
        return text

    beforecharset = "charset="
    aftercharset = '" http-equiv'
    # extract charset
    parsed1 = r.text[r.text.find(beforecharset) + len(beforecharset) :]
    parsed2 = parsed1[: parsed1.find(aftercharset)]
    # Display warning when encoding mismatch
    if parsed2 != r.encoding:
        print("\x1b[1;31;40m" + "Warning: Potential Charset conflict")
        print(" Encoding as extracted by SELF    : " + parsed2)
        print(" Encoding as detected by REQUESTS : " + r.encoding + "\x1b[0m")
        raise ValueError

    # Work around an AGE OLD Python bug in case of windows-874 encoding
    # https://bugs.python.org/issue854511
    if r.encoding == "windows-874" and os.name == "posix":
        print(
            "\x1b[1;31;40m"
            + "Alert: Working around age old Python bug (https://bugs.python.org/issue854511)\nOn Linux, charset windows-874 must be labeled as charset cp874"
            + "\x1b[0m"
        )
        r.encoding = "cp874"

    # convert html tags
    text = html.unescape(r.text)
    # set markers that enclose the wanted translation
    before_trans = 'class="t0">'
    after_trans = "</div><form"
    # extract translation and return it
    parsed1 = r.text[r.text.find(before_trans) + len(before_trans) :]
    parsed2 = parsed1[: parsed1.find(after_trans)]
    # fix parameter strings
    parsed3 = re.sub("% ([ds])", r" %\1", parsed2)
    parsed4 = re.sub("% ([\d]) \$ ([ds])", r" %\1$\2", parsed3).strip()
    translated_string = html.unescape(parsed4).replace("'", r"\'")
    log(f"Translated string = {translated_string}")
    return translated_string


def translate_handling_newlines(
    to_translate, to_language, language="auto", name="no-name"
):
    array_to_translate = []
    # print(to_translate)
    if "\\n" in to_translate:
        log(f"{name} contains \\n so splitting text")
        array_to_translate = to_translate.split("\\n")
    else:
        array_to_translate.append(to_translate)

    resp_array = []
    text_array = []
    for text in array_to_translate:
        print(f"text being translated(key = {name}) = {text}")
        if text.strip():
            # calling method for translation
            translated_text = translate_text_from_google_api(
                to_translate, to_language, language, name
            )
            resp_array.append(translated_text)
        else:
            print(f"Text is empty")
            resp_array.append(None)

        text_array.append(text)

    return "\\n".join(resp_array)


def perform_asserts_on_text(text):
    assert isinstance(text, str)
    assert text, f"Text(= {text}) is empty."
    assert (
        "\\n" not in text
    ), "Should not contain newline character but at-least one is present for test = {text}"


def translate_text_from_google_web(
    to_translate, to_language, language="auto", name="no-name"
):
    """This subroutine calls Google translate and extracts the translation from
    the html request. This method is flaky
    """

    perform_asserts_on_text(to_translate)

    # send request
    req_url = "https://translate.google.com/m?hl=%s&sl=%s&q=%s" % (
        to_language,
        language,
        urllib.parse.quote(to_translate),
    )
    log("\nrequest url = " + req_url)

    # Making fake user-agent
    # ua = UserAgent(use_cache_server=False,verify_ssl=False)
    # userAgent = ua.random
    # log(f'Randm userAgent = {userAgent}')
    # headers = {"User-Agent": userAgent}
    # cookies = {'GOOGLE_ABUSE_EXEMPTION': 'ID=196d8fb1efebf14e:TM=1601733587:C=r:IP=103.43.112.97-:S=APGng0vxwhbunwAPfP8XSWk9jHovjubUfQ'}
    # headers=headers, cookies=cookies

    return parse_response(requests.get(req_url))


def getIso639LangCode(android_lang_code):
    """Convert language code to google api supported language code

    See https://cloud.google.com/translate/docs/languages
    """
    if android_lang_code == "zh-rTW":
        return "zh-TW"
    elif android_lang_code == "zh-rCN":
        return "zh-CN"
    elif android_lang_code == "pt-rPT":
        return "pt"
    else:
        return android_lang_code


def translate_text_from_google_api(
    to_translate, to_language, input_lang, name="no-name"
):
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """

    perform_asserts_on_text(to_translate)
    log(
        f"Resource value with name = {name}, going to call google api call and text = {to_translate} and to_language = {to_language}"
    )

    env_key_name = "GOOGLE_APPLICATION_SERVICE_ACCOUNT_CREDENTIALS_FOR_TRANSLATION"
    assert (
        env_key_name in os.environ
    ), f"{env_key_name} is not present in os environment variables. You may have to restart to your application if this variable is just added"

    path_for_service_key_for_translation = os.environ[env_key_name]
    log(
        f"Returned env variable for service key path = {path_for_service_key_for_translation}"
    )
    assert (
        path_for_service_key_for_translation.strip()
    ), f"Environment path is not set for {env_key_name}"
    assert os.path.exists(
        path_for_service_key_for_translation
    ), f"File doesn't exists for path {path_for_service_key_for_translation} which is set by {env_key_name}"

    translate_client = google_translate_sdk.Client.from_service_account_json(
        path_for_service_key_for_translation
    )
    if isinstance(to_translate, six.binary_type):
        log(
            f"Resource value with name = {name}, is not of type six.binary_type so decoding it"
        )
        to_translate = to_translate.decode("utf-8")
        log(f"Resource value with name = {name}, new decoded value = {to_translate}")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    iso_639_lang_code = getIso639LangCode(to_language)
    log(f"Resource value with name = {name}, iso_639_lang_code = {iso_639_lang_code}")
    result = translate_client.translate(to_translate, target_language=iso_639_lang_code)
    translated_text = result["translatedText"]
    print(
        f'Translation returned from Google service for name {name} = {translated_text} for input text = {result["input"]}, detected language = {result["detectedSourceLanguage"]}'
    )
    return translated_text


#
# MAIN PROGRAM
#

# import libraries


def make_folder(folder_name, overrite=False):
    if not os.path.exists(folder_name):
        print(f"Make folder {folder_name}")
        os.makedirs(folder_name)
        return True
    else:
        if overrite:
            print(f"Make folder already exist {folder_name}")
            shutil.rmtree(folder_name)
            os.makedirs(folder_name)
            return True
        else:
            return False


def print_element(initial_text, translated_text, name):
    log(f"[{name}] {initial_text} -> {translated_text}")


def translate_node(input_node, out_lang, in_lang, name):
    is_translatable = input_node.get("translatable") != "false"
    log(
        f"translate_node is called and key = {name} is found to be translatable = {is_translatable}"
    )
    # Translating the string tag
    if is_translatable:
        # Here you might want to replace root[i].text by the findall_content function
        # if you need to extract html tags
        # ~ totranslate="".join(findall_content(str(ET.tostring(root[i])),"string"))
        to_translate = input_node.text
        assert to_translate is not None, f"Input text is found to None for key = {name}"
        try:
            translation_result = translate_handling_newlines(
                to_translate, out_lang, in_lang, name
            )
            print_element(to_translate, translation_result, name)
            return translation_result
        except Exception as e:
            traceback.print_exc()
            print(
                f"[ERROR] Key with name = {name} failed to be translated with error = {e}, for out_lang_code = {out_lang} and text = {to_translate}"
            )
            return None
    else:
        return None


def get_previous_string(root, id):
    assert type(id) is str, f"In get_previous_string, id is found to be None"
    if root is None:
        return None
    answer_list = root.findall(f".//string[@name='{id}']")
    if len(answer_list) == 0:
        return None
    else:
        return answer_list[0].text


def get_previous_string_item(tag, root, id, index):
    assert type(id) is str, f"In get_previous_string_item id is not string. id = ${id}"
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


def log_reason_for_translation_req(
    index, previous_translated_text, input_string_id, input_text, file_identifier
):
    if previous_translated_text is None:
        log(
            f"{index}: Not skipping translation for {input_string_id} as in values-{file_identifier}/strings.xml, previous translation not found"
        )
    elif previous_translated_text == input_text:
        log(
            f"{index}: Not skipping translation for {input_string_id} as previous translated text(={previous_translated_text}) present at values-{file_identifier}/strings.xml is exactly same, so it must be copy of english text"
        )


def should_translate(previous_translation, input_text):
    return previous_translation is None or previous_translation == input_text


def make_other_lang_string_file(
    in_lang,
    out_lang_folder_prefix_pair,
    in_file_path,
    out_folder_path,
    forced,
    debug_local,
):
    global debug
    debug = debug_local
    out_lang_code = out_lang_folder_prefix_pair[0]
    folder_suffix = out_lang_folder_prefix_pair[1]
    # create outfile name by appending the language code to the input file name
    # print('in_lang = {0}, out_lang = {1}, in_file_path = {2} and out_folder_path = {3}'.format(in_lang, out_lang, in_file_path, out_folder_path))
    _, tail = os.path.split(in_file_path)
    out_file_path = os.path.join(
        out_folder_path,
        f"values-{folder_suffix}",
        tail,
    )

    print(f"\n\nMaking values-{folder_suffix} folder at {out_file_path}")
    print(f"Trying to Making values-{folder_suffix}")
    if make_folder(os.path.dirname(out_file_path)):
        f"Successfully created folder at {out_file_path}"
    else:
        f"Folder was already present at {out_file_path}"
    print("\n")

    # read xml structure
    print(f"Input string file name = {in_file_path}\n")
    input_tree = ET.parse(in_file_path)
    input_tree_root = input_tree.getroot()
    input_tree_working = copy.deepcopy(input_tree)
    input_tree_root_working = input_tree_working.getroot()

    # trying to read output xml if that exists
    if os.path.exists(out_file_path):
        log(f"File path values-{folder_suffix} does contain the strings.xml")
        output_tree = ET.parse(out_file_path)
        output_tree_root = output_tree.getroot()
    else:
        output_tree = None
        output_tree_root = None
        log(f"File path values-{folder_suffix} doesn't contain the strings.xml")

    # cycle through elements
    working_index = 0
    for i in range(len(input_tree_root)):
        # for each translatable string call the translation subroutine
        # and replace the string by its translation,
        # descend into each string array
        log("\n")

        input_node = input_tree_root[i]
        output_node = input_tree_root_working[working_index]

        # If comment then continue
        if not isinstance(input_node.tag, str):
            working_index = working_index + 1
            continue

        string_id = input_node.attrib["name"]
        print(f"{i}: Resource value with name = {string_id}, checking")
        # Translating the string tag
        if input_node.tag == "string":
            print(f"{i}: Resource value with id = {string_id}, found to be string")

            if not input_node.text.startswith("@string/"):
                previous_translated_text = get_previous_string(
                    output_tree_root, string_id
                )
                if should_translate(
                    previous_translation=previous_translated_text,
                    input_text=input_node.text,
                ):
                    log_reason_for_translation_req(
                        i,
                        previous_translated_text,
                        input_string_id=string_id,
                        input_text=input_node.text,
                        file_identifier=folder_suffix,
                    )
                    translated_result = translate_node(
                        input_node, out_lang_code, in_lang, string_id
                    )
                    if translated_result is not None:
                        print(
                            f"{i}: Resource value with name = {string_id}, we are able to complete the translation and result is = {translated_result}"
                        )
                        output_node.text = translated_result
                    else:
                        if input_node.get("translatable") == "true":
                            # Only logging when translatable is true o/w for false value is expected
                            log(
                                f"{i}: [ERROR] Resource value with name = {string_id}, we are NOT able to complete the translation"
                            )
                        input_tree_root_working.remove(output_node)
                        working_index = working_index - 1
                else:
                    print(
                        f"{i}: Resource value with name = {string_id}, skipped as previous translation(= {previous_translated_text}) was found"
                    )
                    output_node.text = previous_translated_text
            else:
                print(
                    f"{i}: Resource value with name = {string_id}, skipped as it is @string/* type value"
                )
        else:
            print(
                f"{i}: Resource value with name = {string_id}, skipped as it is not string may be handled in string-array or plurals"
            )

        # Translating the string-array tag
        if input_node.tag == "string-array" or input_node.tag == "plurals":
            log(f"processing {input_node.tag}")

            for j in range(len(input_node)):
                # for each translatable string call the translation subroutine
                # and replace the string by its translation,

                assert (
                    input_node[j].tag == "item"
                ), f"For {j} index of the type = {input_node.tag} is not item"
                if not input_node[j].text.startswith("@string/"):
                    previous_string = get_previous_string_item(
                        input_node.tag, output_tree_root, string_id, j
                    )
                    if should_translate(
                        previous_translation=previous_string,
                        input_text=input_node[j].text,
                    ):
                        log_reason_for_translation_req(
                            index=i,
                            file_identifier=folder_suffix,
                            input_string_id=string_id,
                            input_text=input_node[j].text,
                            previous_translated_text=previous_string,
                        )
                        output_node[j].text = translate_node(
                            input_node[j],
                            out_lang_code,
                            in_lang,
                            input_node.attrib["name"],
                        )
                    else:
                        output_node[j].text = previous_string

        working_index = working_index + 1
        log(
            f"{i}: Resource value with name = {string_id}, end processing for this node"
        )

    # write new xml file
    print(f"Writing to fileName = {out_file_path}")
    input_tree_working.write(out_file_path, encoding="utf-8", xml_declaration=True)


def main(argv):
    global debug
    parser = argparse.ArgumentParser(
        description="This is a python module to automatically make string.xml file for different languages for Android"
    )
    parser.add_argument(
        "-o",
        action="store",
        default="",
        help="specify the absolute path of the output folder. Default absolute path will be parent folder of the folder containing the strings.xml file",
    )
    parser.add_argument(
        "-i",
        action="store",
        help="specify the absolute path of input file",
        required=True,
    )
    parser.add_argument(
        "-lang",
        action="store",
        default="",
        help="specify the comma-separated languages, ex: -lang 'en,it'. In case no value is provided, will calculate the applicable values from all the values folder and proceed if that is not empty",
    )
    parser.add_argument(
        "-f",
        action="store_true",
        default=False,
        help="force to redo the translation of all the key values, default = False",
    )
    parser.add_argument(
        "-p",
        action="store",
        dest="pool",
        default=5,
        type=int,
        help="set the number of process pool to use, default = 5",
    )
    parser.add_argument(
        "-v",
        action="store_true",
        dest="debug",
        default=False,
        help="enable the debug logs, default = False",
    )

    args = parser.parse_args(argv)
    debug = args.debug

    print("\nScript run started:\n")
    log("\nDebug logs are enabled. Be prepared to bombarded by the terminal logs\n")
    print(f"Current script running path = {os.getcwd()}")

    if not os.path.exists(args.i):
        print(f"Input path({args.i}) doesn't exists so exiting the program\n")
        parser.print_help(sys.stderr)
        sys.exit()

    if os.path.isdir(args.i):
        print(f"Input path({args.i}) is directory so exiting the program\n")
        parser.print_help(sys.stderr)
        sys.exit()

    if not args.o.strip():
        grand_parent_folder = os.path.dirname(os.path.dirname(args.i))
        args.o = grand_parent_folder
        log(f"Directory path of provided input file {grand_parent_folder}")
        make_folder(args.o)
        print(f"Output folder path not provided! Using output path = {args.o}")

    if args.lang == "":
        derived_lang = string_fileutils.get_lang_codes_from_values_folders(args.o)
        if len(derived_lang) == 0:
            print(
                f"Couldn't find any lang code to process and none is given in the argument"
            )
            parser.print_help(sys.stderr)
            sys.exit()
        else:
            args.lang = derived_lang
            print(f"No lang codes is given so calculated {args.lang} to process")

    with Pool(args.pool) as p:
        array_lang = str(args.lang).split(",")
        array_lang_folder_prefix_pair = list(
            map(lambda it: (it.strip().split("-")[0], it.strip()), array_lang)
        )
        log(f"languages provided for translation = {array_lang_folder_prefix_pair}")
        arg_map = map(
            lambda it: ("en", it, args.i, args.o, args.f, debug),
            array_lang_folder_prefix_pair,
        )
        p.starmap(make_other_lang_string_file, arg_map)


if __name__ == "__main__":
    main(sys.argv[1:])
    print("\nOn your right cap!")
