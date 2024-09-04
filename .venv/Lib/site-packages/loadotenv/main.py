import os


def load_env(file_loc=".env"):
    with open(file_loc) as f:
        env_vars = [
            var.strip("\n").split("=") for var in f.readlines()
            if "=" in var  # is a valid variable
            and "#" not in var  # Is not a comment
            and var.count("=") == 1  # Is a valid variable (only 1 `=`)
        ]

        for k, v in env_vars:
            os.environ[k] = v
