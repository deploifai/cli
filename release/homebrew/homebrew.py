def parse_resource_stanzas_from_formula(formula):
    """Parse the resource stanzas from the formula."""
    stanzas = []
    not_end = False

    for line in formula:
        s = line.lstrip()
        if s.startswith("resource"):
            stanzas.append(line)
            not_end = True
        elif not_end:
            stanzas[-1] += line
            if s.startswith("end"):
                stanzas[-1] += "\n"
                not_end = False

    return stanzas


def generate_new_formula(placeholder_formula, resource_stanzas):
    """Generate the new formula."""

    new_formula = []

    for line in placeholder_formula:
        if line.lstrip().startswith("## RESOURCES ##"):
            new_formula += resource_stanzas
        else:
            new_formula.append(line)

    return new_formula


if __name__ == "__main__":
    formula_file = open("deploifai.rb", "r")
    resource_stanzas = parse_resource_stanzas_from_formula(formula_file.readlines())
    formula_file.close()
    print(f"Number of resource stanzas: {len(resource_stanzas)}")

    placeholder_formula_file = open("deploifai.placeholder.rb", "r")
    new_formula = generate_new_formula(
        placeholder_formula_file.readlines(), resource_stanzas
    )
    placeholder_formula_file.close()
    print(f"Number of lines in new formula: {len(new_formula)}")

    new_formula_file = open("deploifai.rb", "w")
    new_formula_file.writelines(new_formula)
    new_formula_file.close()
    print("New formula written to deploifai.rb")
