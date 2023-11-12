# import(s)
import pandas as pd

# compare and compute
with open("mapping", "r") as f:
    contents = f.readlines()

total_acc = 0
year_acc = 0
major_acc = 0

for line in contents:
    # read mapping lines and get file name and expected results
    fname = line.split(".mp4:")[0]
    results = line.split(".mp4:")[1].replace("\n", "").split(",")
    if results[1] == "freshman":
        results[1] = "freshmen"

    # fetch csv for the given file name
    results_model = pd.read_csv("output_bucket/" + fname + ".csv")

    # compare results and store accuracy
    if (results[0] == results_model.iloc[0]["major"]) and (
        results[1] == results_model.iloc[0]["year"]
    ):
        total_acc += 1
        year_acc += 1
        major_acc += 1
    else:
        print(fname, results)
        print(results_model)
        if results[0] == results_model.iloc[0]["major"]:
            major_acc += 1
        if results[1] == results_model.iloc[0]["year"]:
            year_acc += 1


# display
print("accuracy:", str(total_acc) + "%")
