from bcb import sgs
from datetime import date
import const

class Investimento:
    def __init__(self, valor_inicial: float, data_inicio: date, tipo_ativo: str):
        self.valor_inicial = valor_inicial
        self.data_inicio = data_inicio
        self.tipo_ativo = tipo_ativo
        self.tem_imposto = tipo_ativo not in ("LCI", "LCA", "CRI", "CRA", "Poupança")

    def calcular_valor_bruto(self):
        df_cdi = sgs.get(12, start=self.data_inicio, end=date.today().strftime("%Y-%m-%d"))
        percentual_contratado = 1.2  # Ex: 105% do CDI
        fatores = 1 + (df_cdi / 100) * percentual_contratado
        fator_total = fatores.prod().values[0]
        valor_bruto = self.valor_inicial * fator_total
        return valor_bruto

    def calcular_impostos(self):
        valor_bruto = self.calcular_valor_bruto()
        lucro_bruto = max(0.0, valor_bruto - self.valor_inicial)
        dias_corridos = (date.today() - self.data_inicio).days

        # Ativos isentos (LCI, LCA, CRI, CRA)
        if not self.tem_imposto:
            return {
                "iof": 0.0,
                "ir": 0.0,
                "aliquota_ir": 0.0,
                "valor_liquido": valor_bruto,
                "lucro_liquido": lucro_bruto
            }

        # 1. Cálculo de IOF (incide primeiro sobre o lucro)
        iof = 0.0
        if dias_corridos < 30 and dias_corridos > 0:
            aliquota_iof = const.TABELA_IOF[dias_corridos - 1]
            iof = lucro_bruto * aliquota_iof

        base_ir = max(0.0, lucro_bruto - iof)

        # 2. Alíquota de IR pela tabela regressiva
        if dias_corridos <= 180:
            aliquota_ir = 0.225
        elif dias_corridos <= 360:
            aliquota_ir = 0.20
        elif dias_corridos <= 720:
            aliquota_ir = 0.175
        else:
            aliquota_ir = 0.15

        ir = base_ir * aliquota_ir
        imposto_total = iof + ir
        valor_liquido = valor_bruto - imposto_total
        lucro_liquido = valor_liquido - self.valor_inicial

        return {
            "iof": round(iof, 2),
            "ir": round(ir, 2),
            "aliquota_ir": aliquota_ir * 100,
            "valor_liquido": round(valor_liquido, 2),
            "lucro_liquido": round(lucro_liquido, 2)
        }