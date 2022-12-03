import os


def __should_allow_values_folder(values_folder_name, output_absolute_path):
    disallowed_values_folder = ["values-night"]
    return (
        values_folder_name.startswith("values-")
        and values_folder_name not in disallowed_values_folder
        and os.path.exists(
            os.path.join(output_absolute_path, values_folder_name, "strings.xml")
        )
    )


def get_lang_codes_from_values_folders(output_absolute_path):
    list_of_folders = os.listdir(output_absolute_path)
    values_folder = filter(
        lambda it: __should_allow_values_folder(it, output_absolute_path),
        list_of_folders,
    )
    string_identifier_names = map(
        lambda it: it.split("values-")[1],
        values_folder,
    )
    return ",".join(string_identifier_names)
