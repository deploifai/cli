import semver


def compare(input_list):
    given_list = input_list.copy()
    for i in range(len(given_list)):
        for j in range(i + 1, len(given_list)):
            if semver.compare(given_list[i], given_list[j]) == 1:
                temp = given_list[i]
                given_list[i] = given_list[j]
                given_list[j] = temp
    temp = []
    for i, x in enumerate(input_list):
        if x == given_list[-1]:
            temp.append(i)
    return temp, given_list


def multi_compare(version_list, index_list):
    new = {}
    for i in index_list:
        new[i] = version_list[i]
    index = list(new.keys())
    py_value = list(new.values())
    value = py_value.copy()
    for i in range(len(value)):
        for j in range(i + 1, len(value)):
            if semver.compare(value[i], value[j]) == 1:
                temp = value[i]
                value[i] = value[j]
                value[j] = temp
    temp = -1
    for i, x in enumerate(py_value):
        if x == value[-1]:
            temp = i
    index_value = index[temp]
    return index_value
