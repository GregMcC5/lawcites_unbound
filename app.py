import streamlit as st
import requests
from fuzzywuzzy import fuzz
import io
import csv

global uploaded_inventory
uploaded_inventory = None

def get_include_index(data):
    # this function returns the index of the "Include On Chicago Unbound" heading, wherever it may lie in a given input file.
    # this helps prevent issues when someone strips out blank columns in a a file.
    headers = data[0]
    return headers.index("Include On Chicago Unbound")

def author_count(data):
    max = 1
    for line in data[1:]:
        author_count = line[5].lower().count("(auth)")
        if author_count > max:
            max = author_count
    return max

def list_to_csv_string(data):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()

def read_csv(filepath, encoding='utf-8', newline='', delimiter=','):
    with open(filepath, 'r', encoding=encoding, newline=newline) as file_obj:
        data = []
        reader = csv.reader(file_obj, delimiter=delimiter)
        for row in reader:
            data.append(row)

        return data
        
def write_csv(filepath, data, headers=None, encoding='utf-8', newline=''):
    with open(filepath, 'w', encoding=encoding, newline=newline) as file_obj:
        writer = csv.writer(file_obj)
        if headers:
            writer.writerow(headers)
            for row in data:
                writer.writerow(row)
        else:
            writer.writerows(data)

def preprocess_data(data):
    #-Get File
    if not data:
        st.warning("Error", "Please select both input and output files.")
        return

    print("starting processing")

    file = data
    headers = file[0]

    #Get_inventory

    if uploaded_inventory:
        inven_text = uploaded_inventory.read().decode('utf-8')
        inventory = [x.split(",") for x in inven_text.splitlines()]
        write_csv("inventory.csv", inventory)
    else:
        inventory = read_csv("inventory.csv")

    
    #-Initial Filter
    file = [x for x in file if x[file[0].index("Include On Chicago Unbound")].lower() == "true" and not x[file[0].index("Chicago Unbound URL")]]

    #Next Filter
    ready_file = [headers]
    review_file = [headers]

    for line in file:
        flag = False

        # Question Mark check
        q_count = line[headers.index("Article Title")].count("?") if line[headers.index("Source Type")] != "Book" else line[headers.index("Book Title")].count("?")
        if q_count > 4:
            flag = True

        if not line[headers.index("Citation Year")]:
            flag = True

        # Fuzzy Check
        for entry in inventory:
        
            if all([line[headers.index("Generic Citation")], entry[1]]):
                if fuzz.ratio(line[headers.index("Generic Citation")], entry[1]) > 95:
                    flag = True
                    break
            elif not all([line[headers.index("Generic Citation")], entry[1]]):
                lawcites_title = line[headers.index("Article Title")] if line[headers.index("Source Type")] != "Book" else line[headers.index("Book Title")]
                if fuzz.ratio(lawcites_title, entry[0]) > 95:
                    flag = True
                    break
            else:
                flag = True
        if not flag:
            ready_file.append(line)
        else:
            review_file.append(line)

    # output_location = output_entry.get()
    # output_location = "/".join([x for x in output_entry.get().split("/")][:-1] + ["review.csv"])
    # mu.write_csv(output_location, review_file)

    st.markdown("The file below includes files requiring manual review.")
    st.download_button(
                 label="Download Review File",
                 data=list_to_csv_string(review_file),
                 file_name="review.csv",
                 mime="text/csv")
    
    
    
    return ready_file

def isbad(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    if "doi" in url.lower():
        try:
            doi = "/".join(url.split(".org")[1:]).strip("/")
            return not 200 <= requests.get(f"https://api.crossref.org/works/{doi}/", allow_redirects=True).status_code < 300
        except:
            return True
    else:
        try:
            response = requests.get(url, allow_redirects=True, headers=headers)
            return not 200 <= response.status_code < 300
        except requests.RequestException:
            return True

#--Convert Function--

def convert_book(data):
    st.toast("Processing Books", icon="📚")
    if data:
        max = author_count(data)

    #-prepping output data
    output_data = [["title", "custom_citation", "publication_date", "publisher", "book_editors", "fulltext_url", "source_fulltext_url", "catalog_url", "document_type"]]
    for i in range(1, max + 1):
        output_data[0].extend([f"author{i}_fname", f"author{i}_lname"])

    
    for line in data[1:]:
        if line[get_include_index(data)].lower().strip() == "true":  #true test for "include in chicago unbound"
            #normal data
            new_line = [
                line[9],
                line[6],
                line[21],
                line[10],
                "", #<--- will be "book-editors"
                "", #<--- Will be fulltext_url
                "", #<--- Will be source_fulltext_url
                f"http://pi.lib.uchicago.edu/1001/cat/bib/{line[27] if line[27] else line[26]}" if any([line[27],line[26]]) else "", #<--- Will be catalog_url
                "book"] 

            #-Extract Editors
            if "(Ed)" in line[5]:
                editors = [x.replace("(Ed)", "").strip() for x in line[5].split(",") if "(Ed)" in x]
                if len(editors) == 1:
                    new_line[4] = editors[0]
                elif len(editors) > 1:
                    new_line[4] = ", ".join(editors[:-1]) + " & " + editors[-1]

            #----Link Work Begins
            ext_url = []
            for field in [line[25],line[29],line[31],line[23]]:
                if field is not None:
                    if " " in field.strip(" "):
                        link = field.strip(" ").split(" ")[0]
                    else:
                        link = field

                    #-if pdf, goes to fulltext_url
                    if ".pdf" in link.lower() and line[5] is None:
                        new_line[5] = link
                    else:
                        if "http" in link:
                            ext_url.append(link)

            #-sorting out external links for source_fulltext_url
            #-if one


            if len(ext_url) == 1:
                new_line[6] = ext_url[0]

                # if verify_links is True:
                #     if isbad(ext_url[0]) in [True, None]:
                #         st.warning(f"Broken link found:\n---\n{ext_url[0]}\n---\nDo you want to fix the link?")
                #         input_url = st.text_input("Enter the new URL", ext_url[0])
                #         if st.button("Fix Link"):
                #             if input_url:
                #                 new_line[6] = input_url
                #                 st.success(f"Link updated to: {input_url}")
                #             else:
                #                 new_line[6] = ext_url[0]
                #         else:
                #             new_line[6] = ext_url[0]
                #     else:
                #         new_line[6] = ext_url[0]
                # else:
                #     new_line[6] = ext_url[0]
                    
            #if multiple
            elif len(ext_url) > 1:
                if len([x for x in ext_url if "doi" in x.lower()]) == 1:
                    new_line[6] = [x for x in ext_url if "doi" in x.lower()][0]
                else:
                    new_links = [x for x in ext_url if not isbad(x)]
                    if len(new_links) == 1:
                        new_line[6] = new_links[0]
                    elif len(new_links) > 1:
                        new_line[6] = new_links[0]
            elif len(ext_url) == 0:
                new_line[6] == ""


                # if verify_links is True:
                #     new_links = [x for x in ext_url if not isbad(x)]
                #     if len(new_links) == 1:
                #         new_line[6] = new_links[0]
                #     elif len(new_links) > 1:
                #         st.warning(f"Multiple links found for {line[9]}\n---\nPlease provide a preferred link.")
                #         input_url2 = st.text_input("Enter the new URL", new_links[0])
                #         if st.button("Fix Link"):
                #             if input_url2:
                #                 new_line[6] = input_url2
                #     elif len(new_links) == 0:
                #         st.warning(f"No working link found for {line[9]}\n---\nPlease provide a preferred link.")
                #         input_url3 = st.text_input("Enter the new URL")
                #         if st.button("Fix Link"):
                #             if input_url3:
                #                 new_line[6] = input_url3
                # else: #<--- if link checking turned off
                #     filter_proxy = [x for x in ext_url if "proxy.uchicago" not in x]
                #     if len(filter_proxy) == 1:
                #         new_line[6] = filter_proxy[0]
                #     elif len(filter_proxy) > 1:
                #         new_line[6] = filter_proxy[0]
                
            #author data
            if line[5].lower().count("(auth)") == 1:
                if "(ed)" in line[5].lower():
                    for name in line[5].split(", "):
                        if "(auth)" in name.lower():
                            fname = name.split(" ")[0].strip()
                            lname = name.split(" ")[1].split("(")[0].strip()
                            new_line.extend([fname, lname])
                else:
                    fname = line[5].split(" ")[0].strip()
                    lname = line[5].split(" ")[1].split("(")[0].strip()
                    new_line.extend([fname, lname])    
            else:
                for val in [x.strip() for x in line[5].split(", ") if "(Auth)" in x]:
                    fname = val.split(" ")[0].strip()
                    lname = val.split(" ")[1].split("(")[0].strip()
                    new_line.extend([fname, lname])
            

            #add editors if no authors found
            if output_data[0].index("author1_lname") not in range(len(new_line)) and "(Ed)" in line[5]:
                if line[5].lower().count("(ed)") == 1:
                    if "(ed)" in line[5].lower():
                        for name in line[5].split(", "):
                            if "(ed)" in name.lower():
                                fname = name.split(" ")[0].strip()
                                lname = name.split(" ")[1].split("(")[0].strip()
                                new_line.extend([fname, lname])
                    else:
                        fname = line[5].split(" ")[0].strip()
                        lname = line[5].split(" ")[1].split("(")[0].strip()
                        new_line.extend([fname, lname])
                else:
                    for val in [x.strip() for x in line[5].split(", ") if "(Ed)" in x]:
                        fname = val.split(" ")[0].strip()
                        lname = val.split(" ")[1].split("(")[0].strip()
                        new_line.extend([fname, lname])

            output_data.append(new_line)

    return output_data


def convert_chapter(data):
    st.markdown("doing chapter!")

def convert_article(data):
    st.markdown("doing article!")


#-------------------------------------------

st.title('LawCites to BePress Converter')

new_inventory_q = st.toggle("Update ChicagoUnbound Inventory file?", value=False)
if new_inventory_q:
    uploaded_inventory = st.file_uploader("Upload Chicago Unbound CSV file", type='csv', help='Default: `inventory.csv`')


material_type = st.radio(
    "Select Material Type:",
    ('Book', 'Book Chapter/section', 'Article')
)

uploaded_input = st.file_uploader("Upload LawCites CSV file", type='csv')
convert = st.button("convert")

if convert and uploaded_input:
        st.success("Converting...")

    
        text = uploaded_input.read().decode('utf-8')
        data = [x.split(",") for x in text.splitlines()]

        stringio = io.StringIO(uploaded_input.getvalue().decode("utf-8"))
        reader = csv.reader(stringio)
        data = list(reader)


        if material_type:
            if material_type == "Book":
                final_data = convert_book(data=preprocess_data(data))
                st.toast("Conversion Complete", icon="✅")
            elif material_type == "Book Chapter/section":
                final_data = convert_book(data=preprocess_data(data))
            elif material_type == "Article":
                final_data = convert_book(data=preprocess_data(data))
                
    
        st.badge("Success", icon=":material/check:", color="green")
        st.download_button(
                label="Download Output XLS",
                data=list_to_csv_string(final_data),
                file_name="output.csv",
            )



    