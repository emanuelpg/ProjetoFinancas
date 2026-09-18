import pandas as pd
from thefuzz import fuzz

class Gasto:
    product_catalog = pd.read_csv("product_data.csv")

    def __init__(self, tipo, name, price, cat, data, pag):
        self.tipo = tipo
        self.name, self.flag = Gasto.search_prod_name(name)
        self.price = price
        self.cat = cat
        self.date = data
        self.metodo = pag
        self.ori_name = name

    def __str__(self, flag=0):
        if flag == 0:
            return f"Gasto: {self.tipo}, {self.name}, {self.price}, {self.cat}, {self.date}, {self.metodo}"
        else:
            return f"Gasto: {self.tipo}, {self.ori_name}, {self.price}, {self.cat}, {self.date}, {self.metodo}"
        
    def _asList(self):
        return [self.tipo, self.name, self.price, self.cat, self.date, self.metodo, self.flag]

    @staticmethod
    def search_prod_name(name):
        cat_copy = Gasto.product_catalog.copy()
        cat_copy["similarity"] = cat_copy['keys'].apply(lambda x: fuzz.token_set_ratio(name, x))
        cat_copy.sort_values(by='similarity', ascending=False, inplace=True, ignore_index=True)

        found = cat_copy.iloc[0]["values"]
        print(f"{name} mapped to {found} with similarity of {cat_copy.iloc[0]["similarity"]}")

        if cat_copy.iloc[0]["similarity"] > 60:
            return found, 1
        else:
            return found, 0

    @staticmethod
    def map_key_value(key, value):
        Gasto.product_catalog.loc[len(Gasto.product_catalog)] = [key, value]