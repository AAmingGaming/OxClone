# OxClone
 A simple tool to scrape Oxford Courses

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