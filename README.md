# OxClone
 A simple tool to scrape Oxford Courses

# Setup
Install required packages with
```shell
pip install -r ./requirements.txt
```
If playwright is being installed for the first time, you may need to also run
```shell
playwright install
```

# Running
execute the main file with
```shell
python3 main.py
```
## Input options
When presented with the input choice
```
Input the base website to scrape:
```
Input the root url you want to scrape from, i.e. the course parent most course category, examples below.

| What to Scrape | Input |
| --------       | ------- |
| Everything     | blank / 'maths' |
| Only Undergrad | 'https://courses.maths.ox.ac.uk/course/index.php?categoryid=804' |
| Only GR2       | 'https://courses.maths.ox.ac.uk/course/view.php?id=5593' |

\
The user is also presented with the option to download / skip the archival pages (most of the content here is duplicate).
```
Download Arhcives? (y/n):
```

## Console output
As the program is running, status information is output to the console.

Initially the program goes through a scraping phase where it finds the course pages and thier hierarchical structure the following output:
```
3 Sub-Categories in: /Undergraduate/Prelims
9 Sub-Categories in: /Undergraduate/Prelims/Michaelmas
7 Sub-Categories in: /Undergraduate/Prelims/Hilary
2 Sub-Categories in: /Undergraduate/Prelims/Trinity
```
Says while searching Undergraduate/Prelims 3 other categories were found (namely Michaelmas, Hillary, and Trinity). Then while exporing each of these branches even more courses/subcategories were found. Since the program didnt branch deeper, we know it found 9, 7, and 2 **courses** in Michealmas, Hillary, and Trinity respectively.

After finding the pages, the program then goes through each of them to find any files on that page e.g. pdfs, example code, and other text. The number of files found in each course page is output to the console.

```
Found   2 files: ./output/Undergraduate/Induction/Part C and OMMS Induction (202425)
Found  26 files: ./output/Undergraduate/Prelims/Michaelmas/Prereading and summer work (202425)
Found   7 files: ./output/Undergraduate/Prelims/Michaelmas/Introduction to University Mathematics (202425)
```
Here the console ouput suggests that in the `Introduction to University Mathematics (202425)` course, there were 7 files which were found and attempted to download. If there are any issues while downloading the files e.g. permission error's etc, this is also sent ot the console.

e.g.
```
Unexpected status while downloading file: https://weblearn.ox.ac.uk/access/content/group/oxam//uploads/2002/E/7302.pdf
```


# Output
By defualt the scraper outputs to the local folder './output/' which **cannot exist** before running the tool.

To change the output directory, in `main.py` in the `main` function, there is a variable to define where the root of the output will be.
`output_path = "./output/"`

The output itself will mimic the tree/category structure on moodle. A copy of the page itself is made as `source.html` so text / other descriptions on the page are saved, and any pdf's linked, added as a resourse, in a folder, or as part of an assignment are automatically donwloaded.

### Example output
```
output/
├─ Michaelmas/
│  ├─ A0 Linear Algebra (202425)/
│  │  ├─ A0LinearAlgebra20242025.pdf
│  │  ├─ quest1A0.pdf
│  │  ├─ quest2A0.pdf
│  │  ├─ quest3A0.pdf
│  │  ├─ quest4A0.pdf
│  │  ├─ source.html
│  ├─ A1 Differential Equations 1 (202425)/
|  |  ├─ ...
|  ├─ A2.1 Metric Spaces (202425)/
|  |  ├─ ...
|  ├─ ...
├─ Hillary/
|  ├─ ...
├─ Trinity/
|  ├─ ...
```