import requests

from bs4 import BeautifulSoup

DO_ARCHIVES = True


def strip_schema(url: str) -> str:
    return url.split('http://', 1)[-1].split('https://', 1)[-1]


def scrape(root, tag=""):
    resp = requests.get(root)
    
    # check valid status
    if resp.status_code != 200:
        print(f"Invalid response code returned ({resp.status_code}), check the url.")
    
    # Find the 
    tree = find_links(resp.content)
    if tag is None:
        print(f"{len(tree)}: {resp.url}")
    else:
        print(f"{len(tree)}: {tag}")
    tree = domain_expansion(tree, tag)
    return tree
    

def domain_expansion(tree: dict, tag) -> dict:
    for name, href in tree.items():
        # Link examples
        #   Category: https://courses.maths.ox.ac.uk/course/index.php?categoryid=807
        #   Course: https://courses.maths.ox.ac.uk/course/view.php?id=5479
        
        # Checks for archived courses and skips if flag is set.
        if not DO_ARCHIVES and name == "Archive":
            print("Skipping Archives!")
            continue
        
        if "view.php?id=" in href:
            # course, do nothing
            continue
        elif "index.php?categoryid=" in href:
            # category
            tree[name] = scrape(href, tag+"/"+name)
        else:
            print(f"Unexpected link: {name}, {href}")
        
    if not DO_ARCHIVES and "Archive" in tree.keys():
        tree.pop("Archive")
        
    return tree
        

def find_links(content) -> dict:
    # given a connection response, find the links to courses / course categories
    soup = BeautifulSoup(content, 'html.parser')
    
    all_divs = soup.find_all("div")
    filtered_divs = [div for div in all_divs if "class" in div.attrs.keys() and (div["class"] == "category notloaded with_children collapsed".split() or div["class"] == ["coursename"])]
    filtered_cats = {div.a.string: div.a['href'] for div in filtered_divs}
    
    #print(filtered_cats)
    return filtered_cats


def download_pdf():
    pass        


def main():
    global DO_ARCHIVES
    
    # Get root website
    root_url = input("Input the base website to scrape:").strip().lower() or "maths"
    
    if strip_schema(root_url) in ["maths", "math", "courses.maths.ox.ac.uk", "courses.maths.ox.ac.uk/course/index.php?categoryid=0"]:
        root_url = "https://courses.maths.ox.ac.uk/course/index.php?categoryid=0"
        DO_ARCHIVES = input("Download Arhcives? (y/n): ").lower().strip() == "y"
        
    # Ensures a schema is present
    if not root_url.startswith("http"):
        root_url = "http://" + root_url  # assume not secure
        
    course_structrue = scrape(root_url, "")
    print(course_structrue)
    print("End")
    

if __name__ == "__main__":
    main()