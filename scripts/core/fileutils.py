import os


def get_lang_codes_from_values_folders(output_absolute_path):
    disallowed_values_folder = ["values-night"]
    list_of_folders = os.listdir(output_absolute_path)
    values_folder = filter(
        lambda it: it.startswith("values-") and it not in disallowed_values_folder,
        list_of_folders,
    )
    string_identifier_names = map(
        lambda it: it.split("values-")[1],
        values_folder,
    )
    return ",".join(string_identifier_names)
