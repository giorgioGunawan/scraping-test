import scrapy
from ..items import AldiscrapingItem
import re

class AldiSpider(scrapy.Spider):
    name = 'aldi-spider'
    start_urls = ['https://www.aldi.com.au/']
    main_url = 'https://www.aldi.com.au/'
    [find_child, end_child] = [False,False]
    links = []
    parse_index = 0

    def get_list_index(self, response, keyword):
        # Get the text on the navigation item
        categories = response.xpath('//nav/ul/li/div/a[2]/text()').getall()
        index = categories.index(keyword)
        return index

    def get_child_links(self, response):
        # Scrape for children links
        div_root = '//div[contains(concat( " ", @class, " " ), concat( " ", "csc-textpic-left", " " ))]'
        a_tag = '//a/@href'
        children_links = response.xpath('//li[2]/div[2]/ul/li/div/a').getall()

    def get_child_elements(self, response, links, i=0):
        while i < len(links):
            if 'main-nav' in links[i]:
                links.pop(i+1) # Pop out the duplicate
                return response.follow(links[i], callback=self.get_child_links)
            i += 1
        return links

    def navigate_children(self, i):
        # get the next link
        next_link = AldiSpider.links[i]

        # Pop out the duplicate link since we do not need it
        del AldiSpider.links[i + 1:i + 2]

        # Toggle flag and assign index to insert children links
        AldiSpider.find_child = True
        AldiSpider.current_index = i

        # get the Groceries category to check when getting children links
        AldiSpider.children_keyword = next_link.split('/')[5]
        return next_link

    def add_children_links(self,response):
        div_root = '//div[contains(concat( " ", @class, " " ), concat( " ", "csc-textpic-left", " " ))]'
        a_tag = '//a/@href'
        children_links = response.xpath(div_root + a_tag).getall()

        # in case for liquor
        if(not len(children_links)):
            div_root = '//div[3]/div/div/div/div/a/@href'
            children_links = response.xpath(div_root).getall()

        # in case for baby napkins and pantry/coffee
        if(not len(children_links)):
            div_root = '//div[2]/div/div/div/div/a/@href'
            children_links = response.xpath(div_root).getall()

        # Now if it is still empty, then it has reached the end
        if(not len(children_links)): AldiSpider.end_child = True
        # Add links to item
        AldiSpider.links[AldiSpider.current_index:AldiSpider.current_index] = children_links

    def remove_duplicates(self, i=0):
        while i < len(AldiSpider.links):
            if 'main-nav' in AldiSpider.links[i]:
                AldiSpider.links.pop(i)
            i += 1

    def get_packsize(self, response, title, i):
        if re.findall("([A-Za-z]+[0-9]|[0-9]+[A-Za-z][A-Za-z0-9]*)", title):

                return (re.findall("([A-Za-z]+[0-9]|[0-9]+[A-Za-z][A-Za-z0-9]*)", title))[-1]
        else:
            packsize = response.xpath('//article//a[' + str(i + 1) + ']//span[@class="box--amount"]/text()').get()
            if packsize != None:
                return packsize
            else:
                return " "

    def parse_post(self, response, i=0):
        item = AldiscrapingItem()

        # Initialise item components
        product_category,product_price,product_ppu,product_packsize = [],[],[],[]

        # Get product details
        product_title = response.xpath('//a/div/div/div[2]/div[@class="box--description--header"]/text()').getall()
        product_image = response.xpath('//div/div/div/a/div/div/div/img/@src').getall()

        # Parsing title (must be a function)
        while i < len(product_title):
            product_category.append(str(response))
            product_title[i] = product_title[i].replace('\n','').replace(',','').replace('\t','')

            # Hard coded exceptions for beauty section with many non utf8 characters
            if('LACURA' in product_title[i]): product_title.pop(i)
            elif('\xa0' in product_title[i] or product_title[i] == ''): product_title.pop(i)
            else: i += 1

        # Get decimal and whole numbers
        decimal = response.xpath('//article//a//span[@class="box--decimal"]/text()').getall()
        whole_number = response.xpath('//article//a//span[@class="box--value"]/text()').getall()
        whole_number = [ x for x in whole_number if "c" not in x ]

        i = 0
        while i < len(product_title):

            # Get packsize
            product_packsize.append(AldiSpider.get_packsize(self, response, product_title[i], i))

            # Get price per unit value
            pp_unit = response.xpath('//article//a['+str(i+1)+']//span[@class="box--baseprice"]/text()').get()
            pp_unit_alternative = response.xpath('//article//a[' + str(i + 1) + ']//span[@class="box--amount"]/text()').get()

            # If the price per unit value is not available or not shown at all,
            # append appropriate message
            if pp_unit != None and 'see price' in pp_unit:
                product_ppu.append('not available')
                product_price.append('see price in store*')
            elif pp_unit == None:
                product_ppu.append('not available')
            elif pp_unit != None:
                product_ppu.append(pp_unit)

            # Append price if there price exist
            if i >= len(whole_number):
                product_price.append('see price in store*')

            # Decimal value handling
            elif '$' not in whole_number[i]:
                whole_number[i] = '$0.' + whole_number[i]
                product_price.append(whole_number[i])
                decimal.insert(i, 'dummy')
            elif i >= len(decimal):
                product_price.append(whole_number[i])
            elif pp_unit_alternative != None and 'see' in pp_unit_alternative:
                product_price.append('see price in store*')
                whole_number.insert(i,'dummy_value')
            else:
                product_price.append(whole_number[i] + decimal[i])
            i+=1

        # Put in item
        item['product_title'] = product_title
        item['product_image'] = product_image
        item['product_category'] = product_category
        item['product_price'] = product_price
        item['product_ppu'] = product_ppu
        item['product_packsize'] = product_packsize
        yield item

    def parse(self, response, i=0):

        # 1. First get all the main links from the main page
        if not AldiSpider.find_child:
            index = AldiSpider.get_list_index(self, response, "Groceries") # Get index of "Groceries"
            AldiSpider.links = response.xpath('//li['+str(index+1)+']/div[2]/ul/li/div/a/@href').getall()

            # Manually add laundry-household/#main-nav page since it does not exist
            AldiSpider.links.append('https://www.aldi.com.au/en/groceries/laundry-household/#main-nav')
            while i < len(AldiSpider.links):
                if 'main-nav' in AldiSpider.links[i]:
                    next_link = AldiSpider.navigate_children(self, i)
                    yield response.follow(next_link, callback=self.parse)
                i += 1

        # 2. Then get the children links from categories that contain subcategories
        elif AldiSpider.find_child and not AldiSpider.end_child:

            AldiSpider.add_children_links(self, response)
            yield response.follow(AldiSpider.main_url, callback=self.parse)

        # 3. Loop and navigate to all links
        if AldiSpider.find_child and AldiSpider.end_child:
            AldiSpider.remove_duplicates(self) # remove duplicated links

            while AldiSpider.parse_index < len(AldiSpider.links):
                yield response.follow(str(AldiSpider.links[AldiSpider.parse_index]), callback=self.parse_post)
                AldiSpider.parse_index += 1




