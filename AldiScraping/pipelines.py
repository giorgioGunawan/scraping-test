class AldiscrapingPipeline:
    def process_item(self, item, spider):
        title = item['product_title']
        image = item['product_image']
        category = item['product_category']
        price = item['product_price']
        pp_unit = item['product_ppu']
        packsize = item['product_packsize']
        file = open("data.csv", "a")
        for i in range(len(image) if len(image) <= len(title) else len(title)):
            title_parsed = str(title[i])
            file.write(str(category[i])[42:-2].replace('/', ' ') + "," +
                       title_parsed + ',' + str(price[i]) + "," + str(pp_unit[i]) + ","
                       + str(packsize[i]) + "," + str(image[i]) +"\n")

        file.close()
        return item
