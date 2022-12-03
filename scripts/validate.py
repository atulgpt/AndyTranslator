#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This python script extracts verifies the scripts for same number of positional arguments and for missing translation


from multiprocessing import Pool
import argparse
import re
import sys
from lxml import etree as ET
import os
from xml.sax.saxutils import escape
import core.fileutils as string_fileutils

format_regex = re.compile(
    r"(?:%(?:\d+\$)?s|%(?:\d+\$)?d)"
)  # Making non capturing groups so that findall returns actual result instead of tuple of gropus

debug = False


def log(msg):
    if debug:
        print(msg)


# This subroutine extracts the string including html tags
# and may replace 'root[i].text'.
# It cannot digest arbitrary encodings, so use it only if necessary.


#
# MAIN PROGRAM
#

# import libraries


def isTranslatable(node):
    return node.get("translatable") != "false"


def get_previous_string(root, id):
    if type(id) is not str:
        raise ValueError
    if root is None:
        raise ValueError("Root is None")
    answer_list = root.findall(f".//string[@name='{id}']")
    if len(answer_list) == 0:
        raise ValueError(f"Couldn't find string with {id}")
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
        return answer_list[0][index].text


def match(
    translated_format_identifier,
    english_format_identifier,
    name,
    lang,
    translated_text,
    original_text,
):
    if not translated_text:
        # Case when translated string is empty
        return (name, lang, "String is empty")
    if len(translated_format_identifier) != 0 or len(english_format_identifier) != 0:
        log(
            f"trans_list = {translated_format_identifier} and eng = {english_format_identifier} for name = {name} and lang = {lang}\n"
        )
        for match in english_format_identifier:
            if match not in translated_format_identifier:
                return (
                    name,
                    lang,
                    original_text,
                    translated_text,
                    english_format_identifier,
                )


def contains_warning_char(name, lang, translated_text, original_text):
    if not translated_text:
        # Empty string should not come here
        raise ValueError(
            f"String is empty for name = {name} and text = {original_text}"
        )
        #'-' in translated_text or
    if "&" in translated_text:
        return (name, lang, "Warning characters &", original_text, translated_text)

    if "..." in translated_text:
        return (name, lang, "Warning characters ...", original_text, translated_text)

    regexp = re.compile(r"\d-\d")
    if regexp.search(translated_text):
        return (name, lang, "Warning characters -", original_text, translated_text)

    if "--" in translated_text:
        return (name, lang, "Warning characters --", original_text, translated_text)


def check_xml_escaping(name, lang, translated_text, original_text):
    if not translated_text:
        # Empty string should not come here
        raise ValueError(
            f"String is empty for name = {name} and text = {original_text}"
        )
    if escape(translated_text) != translated_text:
        return (
            name,
            lang,
            "Wrong xml escaping",
            original_text,
            translated_text,
            f"Escaped string: {escape(translated_text)}",
        )


def validate_files(in_lang, out_lang, in_file_path, out_folder_path, debug_local):
    global debug
    debug = debug_local
    # create outfile name by appending the language code to the input file name
    # print('in_lang = {0}, out_lang = {1}, in_file_path = {2} and out_folder_path = {3}'.format(in_lang, out_lang, in_file_path, out_folder_path))
    name, ext = os.path.splitext(in_file_path)
    head, tail = os.path.split(in_file_path)
    out_file_path = os.path.join(out_folder_path, f"values-{out_lang}", tail)

    if not os.path.exists(out_file_path):
        raise FileNotFoundError(f"File with path = {out_file_path} doesn't exist")

    # read xml structure
    log(f"File name = {in_file_path}")
    parser = ET.XMLParser(remove_comments=True)
    input_tree = ET.parse(in_file_path)
    input_tree_root = input_tree.getroot()

    # trying to read output xml if that exists
    try:
        output_tree = ET.parse(out_file_path)
        output_tree_root = output_tree.getroot()
    except FileNotFoundError:
        raise FileNotFoundError(f"File with path = {out_file_path} doesn't exist")

    # cycle through elements
    ans = []
    for i in range(len(input_tree_root)):
        # for each translatable string call the translation subroutine
        # and replace the string by its translation,
        # descend into each string array

        input_node = input_tree_root[i]

        # If comment then continue
        if not isinstance(input_node.tag, str):
            continue

        name_attr = input_node.attrib["name"]
        # Translating the string tag
        if input_node.tag == "string":
            if not input_node.text:
                raise ValueError(
                    f"String with name {name_attr} is empty in en language"
                )
            if (not input_node.text.startswith("@string/")) and isTranslatable(
                input_node
            ):
                previous_translated_text = get_previous_string(
                    output_tree_root, name_attr
                )

                log(
                    f'Validating string with name = {name_attr}, prev string = "{previous_translated_text}" against en  string "{input_node.text}"'
                )
                if previous_translated_text:
                    # Empty string throws exception
                    translated_matches = re.findall(
                        format_regex, previous_translated_text
                    )
                else:
                    translated_matches = []
                english_matches = re.findall(format_regex, input_node.text)
                ans.append(
                    match(
                        translated_matches,
                        english_matches,
                        name_attr,
                        out_lang,
                        previous_translated_text,
                        input_node.text,
                    )
                )
                ans.append(
                    contains_warning_char(
                        name_attr, out_lang, previous_translated_text, input_node.text
                    )
                )
                ans.append(
                    check_xml_escaping(
                        name_attr, out_lang, previous_translated_text, input_node.text
                    )
                )

        # Translating the string-array tag
        if input_node.tag == "string-array" or input_node.tag == "plurals":

            for j in range(len(input_node)):
                # for each translatable string call the translation subroutine
                # and replace the string by its translation,

                if input_node[j].tag == "item":
                    if not input_node[j].text.startswith("@string/") and isTranslatable(
                        input_node[j]
                    ):
                        previous_string = get_previous_string_item(
                            input_node.tag, output_tree_root, name_attr, j
                        )

                        log(
                            f'Validating {input_node.tag} with name = {name_attr}, prev string = "{previous_string}" against en  string "{input_node[j].text}"'
                        )

                        translated_matches = re.findall(format_regex, previous_string)
                        english_matches = re.findall(format_regex, input_node[j].text)
                        ans.append(
                            match(
                                translated_matches,
                                english_matches,
                                name_attr,
                                out_lang,
                                previous_string,
                                input_node[j].text,
                            )
                        )
                        ans.append(
                            contains_warning_char(
                                name_attr,
                                out_lang,
                                previous_translated_text,
                                input_node.text,
                            )
                        )
                        ans.append(
                            check_xml_escaping(
                                name_attr,
                                out_lang,
                                previous_translated_text,
                                input_node.text,
                            )
                        )
                else:
                    raise ValueError
    return ans


flatten = lambda l: [item for sublist in l for item in sublist]


def main(argv):
    global debug
    parser = argparse.ArgumentParser(
        description="This is a python module to verify the same number of positional arguments, missing translation, warning characters(e.g., &, ..., -, --) and wrong xml escaping"
    )
    parser.add_argument(
        "-o",
        action="store",
        default="",
        help="specify the absolute path of the output folder. Default absolute path will be parent folder of the folder containing the strings.xml file",
    )
    parser.add_argument(
        "-i", action="store", help="specify the absolute input file path"
    )
    parser.add_argument(
        "-lang",
        action="store",
        default="",
        help="specify the comma-separated languages, ex: -lang 'en,it'. In case no value is provided, will calculate the applicable values from all the values folder and proceed if that is not empty",
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
        help="enable the debug logs",
    )

    args = parser.parse_args(argv)
    debug = args.debug
    log("Debug logs are enabled. Be prepared to bombarded by the terminal logs")

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
        array_lang_striped = list(map(lambda it: it.strip(), array_lang))
        arg_map = map(lambda it: ("en", it, args.i, args.o, debug), array_lang_striped)
        answers = p.starmap(validate_files, arg_map)
        flatten_ans = flatten(answers)
        filtered = filter(lambda it: it is not None, flatten_ans)
        print(*list(filtered), sep="\n\n")


if __name__ == "__main__":
    main(sys.argv[1:])
    print("\nOn your right cap!")
