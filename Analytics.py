import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import sqlite3
import datetime
import os, sys

from BancoDeDados import DataBase

class Analytics:
    def __init__(self):
        self.db = DataBase()
        self.dir = r"C:\Users\emanu\ProjetoFinanças\Charts"
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def extractMonths(self):
        query = "select distinct strftime('%Y-%m', dia) AS mes " \
        "from gastos " \
        "Order by mes DESC"

        results, _ = self.db.consultaManual(query)

        meses = np.array(results)[:,0]

        return meses

    def gastoPorCategoria(self, curMes=None):
        if curMes is None:
            curMes = datetime.datetime.today().strftime('%Y-%m')
    
        query = "select g.categoria, g.gasto_total from " \
        "(select categoria, strftime('%Y-%m', dia) AS mes, " \
        "SUM(valor) as gasto_total "\
        "FROM gastos "\
        f"where mes = '{curMes}' AND tipo_gasto in ('Gasto Fixo', 'Gasto Não Fixo') "\
        "GROUP BY categoria, mes) as g; "

        result, colunas = self.db.consultaManual(query)
        result = np.array(result)
        if np.ndim(result) == 1:
            result = result.reshape(1, -1)

        categorias = result[:, 0]
        valores = [float(val) for val in result[:, 1]]
        fig_path = os.path.join(self.dir, "categoria.png")

        fig, ax = plt.subplots()

        fig.set_size_inches((5, 3.5))
        ax.set_title("Gastos por Categoria", fontsize=11, fontweight="bold")
        plt.tight_layout()

        barras = ax.barh(categorias, valores)
        max_valor = max(valores) if valores else 100
        ax.set_xlim(0, max_valor * 1.25)  # 20% de margem no topo da barra

        ax.bar_label(
            barras, 
            fmt="R$ %.2f",           # Formata como valor monetário (ex: R$ 254.00)
            label_type="edge",       # "center" coloca no meio da barra; "edge" coloca na ponta
            color="black",            
            fontsize=9, 
            fontweight="bold"
        )

        fig.savefig(fig_path, bbox_inches='tight', dpi=100)

        #plt.show()
        plt.close()

        return result, colunas, fig_path

    def gastoOrcamentario(self, curMes=None):
        if curMes is None:
            curMes = datetime.datetime.today().strftime('%Y-%m')

        """ Orçamento por Tipo """
        query = f"""
            select g.tipo_gasto, g.gasto_total from 
                (select tipo_gasto, strftime('%Y-%m', dia) AS mes, sum(valor) as gasto_total 
                    from gastos 
                    where mes = '{curMes}' AND tipo_gasto in ('Gasto Fixo', 'Gasto Não Fixo', 'Investimento') 
                    group by tipo_gasto, mes) as g
            """

        result_t, colunas_t = self.db.consultaManual(query)
        result_t = np.array(result_t)

        if np.ndim(result_t) == 2:
            tipos = result_t[:, 0]
            valores = [float(val) for val in result_t[:, 1]]
            fig_path_t = os.path.join(self.dir, "orcamento.png")
            
            fig, ax = plt.subplots()
            fig.set_size_inches((5, 3.5))
            ax.pie(valores, labels=tipos, autopct='%1.1f%%')
            ax.set_title(f"Distribuição do Orçamento em {curMes}")
            plt.tight_layout()

            fig.savefig(fig_path_t, bbox_inches='tight', dpi=100)

            plt.close()
        else:
            fig_path_t = None

        """ Orçamento Alimentar """
        query = f"""
            select g.categoria, g.gasto_total from 
                (select categoria, strftime('%Y-%m', dia) AS mes, sum(valor) as gasto_total 
                    from gastos 
                    where mes = '{curMes}' AND categoria  in ('Doce', 'Fruta', 'Comida Pronta', 'Comida para Fazer') 
                    group by categoria, mes) as g
        """

        result_c, colunas_c = self.db.consultaManual(query)
        result_c = np.array(result_c)

        for res in result_c:
            if (res[0] == "Comida Pronta") or (res[0] == "Doce"):
                res = list(res)
                res[0] = "Restaurante/Delivery" 
            else:
                res = list(res)
                res[0] = "Mercado" 

        if np.ndim(result_c) == 2:
            tipos = result_c[:, 0]
            valores = [float(val) for val in result_c[:, 1]]
            fig_path_c = os.path.join(self.dir, "alimentacao.png")
            
            fig, ax = plt.subplots()
            fig.set_size_inches((5, 3.5))
            ax.pie(valores, labels=tipos, autopct='%1.1f%%')
            ax.set_title(f"Alimentação em {curMes}")
            plt.tight_layout()

            fig.savefig(fig_path_c, bbox_inches='tight', dpi=100)

            plt.close()
        else:
            fig_path_c = None
        
        
        return fig_path_t, fig_path_c

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

            query = f"select strftime('%Y-%m', dia) AS mes,"\
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
        

# test = Analytics()
# print(test.gastoOrcamentario())
