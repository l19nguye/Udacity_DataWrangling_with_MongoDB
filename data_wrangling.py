
# coding: utf-8

# In[95]:

import csv
import pprint
import re
import codecs
import xml.etree.cElementTree as ET
import json
from collections import defaultdict
import unicodedata


# In[96]:

# the OSM data file
OSM_FILE = "hochiminh_city.osm"

# the JSON file
JSON_FILE = "hochiminh_city.json"


# In[97]:

'''
Function insert_space_between_words() is written to fix this issue, 
it will add a space character next to a LOWERCASE letter which is followed by an UPPERCASE letter.

We expect insert_space_between_words("ThuDuc") = "Thu Duc"
'''
def insert_space_between_words(text):
    if text != None:
        # convert text into a list
        chars = list(text.strip())
    
        # loop through each character of text
        # if there is any UPPERCASE character is next to a LOWERCASE character --> add index of LOWER character into a list
        ls_indexes = []
        for i in range(len(chars) -1):
            if chars[i].islower() and chars[i+1].isupper():
                ls_indexes.append(i+1)
    
        # now we have a list of indexes
        # we need to add a space character at each index in the list
        if len(ls_indexes) > 0:
            for index in reversed(ls_indexes):
                chars.insert(index, " ")
    
        # join all item of character list, we will have a string, then return it
        return ''.join(chars)
    else:
        return ""


# In[98]:

'''
Function to convert the accented characters to unaccented characters.
'''
def replace_accented_characters(text):
    accent_chars = "ŠŽšžŸÀÁÂÃÄÅẤẦẨẪẬĂẶẲẰẮÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖÙÚÛÜÝàáãạảẵặằắăâậẫẩầấãäåçẻẽẹèéệễểềếểêëịĩỉìíîïðñọõỏòóộôõồöỗổốợỡởờớơủũụùúựữửứừưûüỹỵỳýÿĐđ"
    non_accent_chars = "SZszYAAAAAAAAAAAAAAAACEEEEIIIIDNOOOOOUUUUYaaaaaaaaaaaaaaaaaaaceeeeeeeeeeeeeiiiiiiidnooooooooooooooooooouuuuuuuuuuuuuyyyyyDd"

    for char in text:
        if char in accent_chars:
            text = text.replace(char, non_accent_chars[accent_chars.index(char)])
    return text


# In[99]:

'''
It will get v value of an element which has k value is k_name.
It will find the tag has k value is k_name, then return the v value of that tag if it existing.
'''
def get_value_of_k(element, k_name):
    result = None
    tag = element.find("tag[@k='" + k_name + "']")
    if tag != None:
        result = tag.get('v')
    return result


# In[100]:

'''
Purpose: This function is used for auditing data of a k value.

This function will loop through each element and call function get_value_of_k() to get v value of k.
The outcome would be the list of unique values of those v values
'''
def audit_data_of_k(file_in, k_name):
    data = []
    for element in get_element(file_in, tags=('node', 'way')):
        v = get_value_of_k(element, k_name)
        if v != None:
            data.append(v)
    
    return sorted(list(set(data)))


# In[101]:

'''
This function will create a regular expression for a string.
We will use this function to create regular expression for a PROVINCE or a CITY name.
'''
def create_regex(text):
    reg = ''
    if text != None and text != "":
        reg = "\w*.*\s*" + text + "\s*.*\w*"
    return reg


# In[102]:

'''
This function will create a list regular expression for a list of strings.
It will loop through each string in the list, call function create_regex_for_text() to create regular expression for that string.
All regular expressions created will be store in another list.
'''
def create_list_regex(list_text):
    regex = []
    if len(list_text) > 0:        
        for item in list_text:
            regex.append(create_regex(item.lower()))
    return regex


# In[103]:

'''
Purpose: will replace a existing name with a expected name. 

Input parameters:
    - requires 3 input parameters:
        + name: string type.
        + list_regex: is a list regular expression created from the list of variants.
        + list_expected_names: is a list expected names created from the list of variants and would be used to replace.

*Note: before process the name, need to fix the problems of 1.1 and 1.2.
'''

def replace_name_with_expected_name(name, list_regex, list_expected_names):
    result = None
    for regex in list_regex:
        match = re.match(regex, replace_accented_characters(insert_space_between_words(name)), re.IGNORECASE)
        if match != None:
            result = list_expected_names[list_regex.index(regex)]
            break
    return result


# In[105]:

'''
This function just be used to create a regular expression for DISTRICTS since DISTRICT has some specific prefixes which 
are different from PROVINCE or CITY.

Following are all prefixes would be used for DISTRICT: 
["quan", "quan ", "district ", "d.", "d. ", "d ", "d", "q.", "q. ", "q", "qan ", "huyen " , "^"]

'''

DISTRICT_PREFIXES = ["quan", "quan ", "district ", "d.", "d. ", "d ", "d", "q.", "q. ", "q", "qan ", "huyen " , "^"]

def create_reg_for_a_district(text, prefixes):
    reg = []
    for item in prefixes:
        reg.append(item + text)
    return '|'.join(reg)


'''
This function will create a list of regular expressions for a list of DISTRICTS.
It will call the function make_reg_for_district() to create regular expression for each DISTRICT in list_districts, 
then output are stored in another list.
'''
def create_list_regex_for_districts(list_districts, dist_prefixes):
    result = []
    district_lowercase = [ item.lower().strip() for item in list_districts ]
    for district in district_lowercase:
        reg = create_reg_for_a_district(district, dist_prefixes)
        reg += "|" + create_regex("quan " + district)
        reg += "|" + create_regex("huyen " + district)
        result.append(reg)
    return result


# In[84]:

'''
This function will display a location name in the pretty format like 'Ho Chi Minh City', 'District 1', 'Dong Nai Province'...

It requires 2 input parameters:
    - name: the name of location.
    - unit_type: the type of location, it would be "district" or "city" or "province".

If the name is a numeric value, the output would be: name + unit_type
If not, the output would be:  unit_type + name'''

def format_name(name, unit_type):
    result = ""
    if name != None and name != "":
        if unit_type.lower() in ("district", "city", "province"):
            if name.isnumeric():
                result = (unit_type + " " + name).title()
            else:
                if name.lower() == "ho chi minh":
                    unit_type = "city"
                result = (name + " " + unit_type).title()
    return result


# In[85]:

'''
Purpose: This function will correct the "v" value in <tag> which has "k" = key_name.

Input parameters:
    - element: the focusing element.
    - key_name: the value of "k" atribute in a <tag> of element
    - list_regex: list regular expression would be used for function replace_name_with_expected_name()
    - list_expected_text: list expected text would be used for function replace_name_with_expected_name()

What it is going to do is actually call all above function.

- if there is any <tag> existing:
    + if <tag> has k value is the key_name:
        + unit_type = key_name[5:] since we are focusing on 3 keys ["addr:province", "addr:city", "addr:district"] 
            so unit_type would be "province" or "city" or "district".
        + call function replace_variant_with_expected_name() to replace with the expected name.
        + format name in the pretty format.
        + update the attribute "v" the formatted name.
'''                             
def correct_addr_parts_name(element, k_value, list_regex, list_expected_names):
    tag = element.find("tag[@k='" + k_value + "']")
    if tag != None:
        # get the unit_type
        unit_type = k_value[5:]
        # get the expected name of item
        expected_name = replace_name_with_expected_name(tag.attrib['v'], list_regex, list_expected_names)
        # format the expected name in the pretty format
        pretty_name = format_name(expected_name, unit_type)
        # update the value of v the pretty_name
        tag.set('v', pretty_name)


# In[86]:

# postcodes of PROVINCES
POSTCODES_PROVINCE = {'Ho Chi Minh City' : '700000',
                      'Vung Tau Province' : '790000',
                      'Dong Nai Province' : '810000',
                      'Binh Duong Province' : '590000',
                      'Tien Giang Province' : '860000',
                      'Long An Province' : '850000' }

# postcodes of CITIES
POSTCODES_CITY = {'Ho Chi Minh City' : '700000',
                  'Vung Tau City' : '790000',
                  'Bien Hoa City' : '810000',
                  'Thu Dau Mot City' : '590000',
                  'My Tho City' : '860000',
                  'Tan An City' : '850000' }

# postcodes of Ho Chi Minh's DISTRICTS
POSTCODES_HCM_DISTRICT = {
    'Binh Chanh District' : '709000',
    'Binh Tan District' : '709300',
    'Binh Thanh District' : '704000',
    'Can Gio District' : '709500',
    'Cu Chi District' : '707000',
    'Go Vap District' : '705500',
    'Hoc Mon District' : '707500',
    'Nha Be District' : '708500',
    'Phu Nhuan District' : '704500',
    'District 1' : '701000',
    'District 10' : '703500',
    'District 11' : '706500',
    'District 12' : '707800',
    'District 2' : '708300',
    'District 3' : '701500',
    'District 4' : '702000',
    'District 5' : '702500',
    'District 6' : '703000',
    'District 7' : '708800',
    'District 8' : '706000',
    'District 9' : '708400',
    'Tan Binh District' : '705000',
    'Tan Phu District' : '705800',
    'Thu Duc District' : '708000'
}


# In[87]:

# set v=v_value for the tag which has k=k_value
def update_v_for_k(element, k_value, v_value):
    tag = element.find("tag[@k='" + k_value + " ']")
    if tag != None:
        tag.set('v', v_value)
        
        
# insert a new <tag k=k_value v=v_value> for an element 
def insert_new_tag(element, k_value, v_value):
    new_tag = ET.Element('tag')
    if element.find("tag[@k='" + k_value + " ']") == None:
        new_tag.attrib['k']  = k_value
        new_tag.attrib['v'] = v_value
        element.insert(0, new_tag)


# delete a tag which has k=k_value from an element
def delete_a_tag(element, k_value):
    tag = element.find("tag[@k='" + k_value + "']")
    if tag != None:
        element.remove(tag)
        

'''
Function to correct POSTCODE value for an element.

The idea here is we are just focusing on elements which has tag of "addr:province" or "addr:city" or "addr:district" or "addr:postcode". Then we will do:
    - Step 1: get the POSTCODE value by PROVINCE or CITY or DISTRICT name.
        + if the element has tag of DISTRICT, the POSTCODE would be taken from dictionary POSTCODES_HCM_DISTRICT.
        + if the element has tag of CITY, the POSTCODE would be taken from dictionary POSTCODES_CITY.
        + if the element has tag of PROVINCE, the POSTCODE would be taken from dictionary POSTCODES_PROVINCE.

      so result of this step is a POSTCODE value. It would be a value of one of above dictionaries or None.

    - Step 2: check whether this element has tag of POSTCODE.
        + if it has and:
            - POSTCODE value of Step 1 is None, then we will delete that tag.
            - POSTCODE value of Step 1 is NOT None, then we will update the POSTCODE value into the "v" attribute of the tag.

        + if it does NOT and POSTCODE value of Step 1 is NOT None, we will add a new tag for POSTCODE with the value of Step 1.
'''
def correct_postcode_for_element(element, hcm_district_postcodes, city_postcodes, province_postcodes):
    postcode = None
    
    # list of k values of all tags that element has.
    # we are just focusing on values of "addr:province", "addr:city", "addr:district", "addr:postcode"
    k = [ tag.attrib['k'] for tag in element.findall("tag") if tag.attrib['k'] in ("addr:province", "addr:city", "addr:district", "addr:postcode")]
    
    #################################### START STEP 1 ####################################
    # if element has at least one of those values
    if len(k) > 0:
        # get the POSTCODE by DISTRICT if tag of "addr:district" available in the node
        if "addr:district" in k:
            district = get_value_of_k(element, "addr:district")           
            if district in hcm_district_postcodes:
                postcode = hcm_district_postcodes[district]
        else:
            # get the POSTCODE by CITY if tag of "addr:city" available in the node
            if "addr:city" in k:
                city = get_value_of_k(element, "addr:city")
                if city in city_postcodes:
                    postcode = city_postcodes[city]
            else:
                # get the POSTCODE by PROVINCE if tag of "addr:province" available in the node
                if "addr:province" in k:
                    province = get_value_of_k(element, "addr:province")
                    if province in province_postcodes:
                        postcode = province_postcodes[province]
    #################################### END STEP 1 ####################################
    # so now we have a POSTCODE value, it would be None or NOT None.
    
    
    #################################### START STEP 2 ####################################
    #### decide to insert or update or delete the tag of POSTCODE
    
        if "addr:postcode" in k and postcode == None:
            # if element has tag of POSTCODE and postcode value = None --> delete the tag
            delete_a_tag(element, "addr:postcode")
        elif "addr:postcode" in k and postcode != None:
            # if element has tag of POSTCODE and postcode value not None --> update the tag
            update_v_for_k(element, "addr:postcode", postcode)
        elif "addr:postcode" not in k and postcode != None:
            # if element does not has tag of POSTCODE and postcode value not None --> add new tag for POSTCODE
            insert_new_tag(element, 'addr:postcode', postcode)
    #################################### END STEP 2 ####################################


# In[107]:

'''
this function will convert the v value from string to a list
'''
def value_to_list(element, k_name):
    result = []
    v = get_value_of_k(element, k_name)
    if v != None:
        if ";" in v:
            result = v.split(";")
        else:
            result.append(v)
    return result

'''
The idea is one element should have only one tag for CUISINE and the k value would be 'cuisine' and v value would be a list.
Here are steps which I will follow:
    - Step 1: check whether element has tag for "cuisine" and "cuisine_1"
    - Step 2: 
        + if element has tag for "cuisine", convert v value into a list.
        + if element has tag for "cuisine_1", convert v value into a list.
        + adding 2 above lists then we will have the result for this step.
    - Step 3: update v value for tag of "cuisine".
    - Step 4: delete the tag of "cuisine_1" if the element has.
'''
def correct_cuisine_for_element(element):
    # get list k values of tags that element has
    # we are just focusing on the k values of "cuisine" and "cuisine_1"
    k1 = [ tag.attrib['k'] for tag in element.findall("tag") if tag.attrib['k'] in ("cuisine" ,"cuisine_1")]
    
    # if the element has at least one of those k values
    if len(k1) > 0:
        values = []
        
        if 'cuisine' in k1:
            values = value_to_list(element, 'cuisine')
        
        if 'cuisine_1' in k1:
            values += value_to_list(element, 'cuisine_1')                    
        
        # update values for tag of 'cuisine'
        update_v_for_k(element, 'cuisine', values)
        
        # remove the tag of 'cuisine_1'
        delete_a_tag(element, 'cuisine_1')


# In[89]:

'''
SHAPING NODE ELEMENT.

The result of one NODE would be a dictionary which has:
    - keys: are attributes of the node and the 'k' values of all tags
    - values: are the attributes' values and the 'v' values of all tags.

Since the element is a NODE, so the result should have "type": "node".

Ex: the result of the following node:

<node id="1001114531" lat="10.8035794" lon="106.7021517" version="3" timestamp="2016-12-05T01:00:20Z" changeset="44169736" uid="4923449" user="Eddy Thiện">
  <tag k="tourism" v="guest_house"/>
  <tag k="internet_access" v="wlan"/>
</node>

should be:

{
 'changeset': '44169736',
 'id': '1001114531',
 'internet_access': 'wlan',
 'lat': '10.8035794',
 'lon': '106.7021517',
 'timestamp': '2016-12-05T01:00:20Z',
 'tourism': 'guest_house',
 'uid': '4923449',
 'user': 'Eddy Thiện',
 'version': '3',
 'type': 'node'
}

Below is the function to extract the data of an element into a dictionary.
'''
def extract_element_data_to_dict(element):
    result = defaultdict()
    if element != None:
        # get data of all attributes
        result = element.attrib
        
        # get v values of all the <tag> which element has
        if element.findall("tag") != None:
            for tag in element.findall("tag"):
                result[tag.attrib['k']]  =  tag.attrib['v']
                
        # get tag name of the element
        result['type'] = element.tag        
    return result


# In[90]:

'''
SHAPING WAY ELEMENT.

The result of one WAY would be a dictionary which has:
    - keys: are attributes of the node and the 'k' values of all tags
    - values: are the attributes' values and the 'v' values of all tags.

Since the element is a NODE, so the result should have "type": "node".
The difference of WAY from the NODE is WAY has number of tags <nd>, each tag <nd> is a NODE ID which related to the WAY.
The result should have "nodes" : [....]

Ex: the result of the following WAY

<way id="311787604" version="1" timestamp="2014-11-08T16:50:29Z" changeset="26646253" uid="509465" user="Dymo12">
  <nd ref="2339295659"/>
  <nd ref="2339295662"/>
  <nd ref="2339295673"/>
  <nd ref="2339295675"/>
  <nd ref="2339295678"/>
  <nd ref="2339295679"/>
  <nd ref="2339332736"/>
  <nd ref="2339295680"/>
  <nd ref="2339332752"/>
  <nd ref="2339295685"/>
  <nd ref="2339332759"/>
  <nd ref="2339295689"/>
  <nd ref="2339332766"/>
  <nd ref="2339332772"/>
  <nd ref="2339332776"/>
  <tag k="highway" v="residential"/>
</way>

should be:
    
{
'id': '311787604', 
'version': '1', 
'timestamp': '2014-11-08T16:50:29Z', 
'changeset': '26646253', 
'uid': '509465', 
'user': 'Dymo12', 
'highway': 'residential', 
'nodes': ['2339295659', '2339295662', '2339295673', '2339295675', 
         '2339295678', '2339295679', '2339332736', '2339295680', 
         '2339332752', '2339295685', '2339332759', '2339295689', '2339332766', '2339332772', '2339332776'],
'type': 'way'
}
 
'''
def extract_way_data_to_dict(way):
    # reuse the function used for NODE to extract data of WAY
    result = extract_element_data_to_dict(way)
    
    # since WAY element might have number of <nd>
    # if element has any <nd>, get ref values and store them in a list
    if way.findall("nd") != None:
        list_ref = [nd.attrib['ref'] for nd in way.findall("nd")]
        result['nodes'] = list_ref
    
    return result


# In[91]:

def shape_element(element, province_regex, city_regex, district_regex, province_expected, city_expected, 
                  district_expected, province_postcodes, city_postcodes, hcm_district_postcodes):    
        
    # correct the PROVINCE names
    correct_addr_parts_name(element, "addr:province", province_regex, province_expected)
        
    # correct the CITY names
    correct_addr_parts_name(element, "addr:city", city_regex, city_expected)
        
    # correct the DISTRICT names
    correct_addr_parts_name(element, "addr:district", district_regex, district_expected)
    
    # correct POSTCODE
    correct_postcode_for_element(element, hcm_district_postcodes, city_postcodes, province_postcodes)
        
    # correct CUISINE
    correct_cuisine_for_element(element)
    
    # shape element data
    if element.tag == "node":
        return extract_element_data_to_dict(element)
    elif element.tag == "way":
        return extract_way_data_to_dict(element)


# In[92]:

#################################### CASE STUDY's FUNCTION ####################################
def get_element(osm_file, tags=('node', 'way')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# In[106]:

# list variant names of PROVINCE
PROVINCE_VARIANTS =  ['binh duong', 'vung tau', 'ho chi minh', 'hcm', 'long an', 'tien giang', 'dong nai']

# list expected names of PROVINCE
PROVINCE_EXPECTED = ['Binh Duong', 'Vung Tau', 'Ho Chi Minh', 'Ho Chi Minh', 'Long An', 'Tien Giang', 'Dong Nai']

# list variant names of CITY
CITY_VARIANTS = ['vung tau', 'ho chi minh', 'saigon','hcm','hcmc', 'ho chi min', 'bien hoa', 'thu dau mot', 'my tho', 'tan an']

# list expected names of CITY
CITY_EXPECTED = ['Vung Tau', 'Ho Chi Minh', 'Ho Chi Minh', 'Ho Chi Minh', 'Ho Chi Minh', 'Ho Chi Minh', 'Bien Hoa', 'Thu Dau Mot', 'My Tho', 'Tan An']

# list expected names of DISTRICT
DISTRICT_EXPECTED  = ['1', '10', '11', '12', '2', '3', '4', '5', '6', '7', '8', '9',
                                 'Binh Chanh', 'Binh Tan', 'Binh Thanh', 'Can Gio', 'Cu Chi', 'Go Vap', 'Hoc Mon',
                                 'Nha Be', 'Phu Nhuan', 'Tan Binh', 'Tan Phu', 'Thu Duc']




'''
Before shaping element data, we need to create the list of regular expressions which will be use
to correct values of PROVINCE, CITY and DISTRICT.
'''
#################################### CASE STUDY's FUNCTION ####################################
def process_map(file_in):
    
    # create list of regular expressions for PROVINCES
    province_regex = create_list_regex(PROVINCE_VARIANTS)
    
    # create list of regular expressions for CITIES
    city_regex = create_list_regex(CITY_VARIANTS)
    
    # create list of regular expressions for DISTRICTS
    district_regex = create_list_regex_for_districts(DISTRICT_EXPECTED, DISTRICT_PREFIXES) 
    
    # list data of all elements
    data = []
   
    # open JSON file for writting data
    with codecs.open(JSON_FILE, encoding='utf-8', mode='w') as file:
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element, province_regex, city_regex, district_regex, PROVINCE_EXPECTED, CITY_EXPECTED, 
                  DISTRICT_EXPECTED, POSTCODES_PROVINCE, POSTCODES_CITY, POSTCODES_HCM_DISTRICT)
            
            # add data of each element into list
            data.append(el)
        
        # writting data into JSON file
        file.write(json.dumps(data, indent=2))


# In[94]:

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_FILE)


# In[ ]:



