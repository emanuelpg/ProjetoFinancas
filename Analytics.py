import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3

from BancoDeDados import DataBase

class Analytics:
    def __init__(self):
        self.db = DataBase()


    def gastoMedioMensal(self):
        meses, _ = [l[0] for l in self.db.consultaManual(
            "select distinct " \
            "strftime('%Y-%m', dia) AS mes" \
            "FROM gastos"
        )]

        review = []
        cols = ["mes", "income", "outcome", "saldo", "variância"]

        for mes in meses:
            income = 0
            outcome = 0

            query = f"select" \
            "strftime('%Y-%m', dia) AS mes,"\
            "SUM(valor) as gasto_total,"\
            "tipo_gasto"\
            "FROM gastos"\
            "where mes = {mes} "\
            "GROUP BY tipo_gasto, mes"\
            "ORDER BY mes DESC;"

            result, _ = self.db.consultaManual(query)

            for l in result:
                if l[-1] in ("Gasto Fixo", "Gasto Não Fixo"):
                    outcome += l[1]
                if l[-1] == "Income":
                    income += l[1]

            review.append(np.array([mes, income, outcome, income-outcome]))

        mean = np.mean(np.array(review)[:, -1])
        for l in review:
            review = np.concatenate(l, [l[-1]-mean])

        return review, cols
        

a =[[2, 3], [4, 5]]
print(np.array(a)[:, -1])


