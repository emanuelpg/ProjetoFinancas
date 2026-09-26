from bcb import sgs
from datetime import date
import const

import numpy as np

class Investimento:
    def __init__(
        self,
        nome: str,
        valor_inicial: float,
        data_inicio: date,
        tipo_ativo: str,
        data_vencimento: date = None,
        tipo_taxa: str = "CDI",
        percentual_contratado: float = 100.0,
        taxa_adicional_ipca: float = 0.0  # Ex: 6.0 para IPCA + 6.0% a.a.
    ):
        self.nome = nome
        self.valor_inicial = float(valor_inicial)
        self.data_inicio = data_inicio
        self.data_vencimento = data_vencimento
        self.tipo_ativo = tipo_ativo
        self.tipo_taxa = tipo_taxa
        self.percentual_contratado = float(percentual_contratado)
        self.taxa_adicional_ipca = float(taxa_adicional_ipca)
        self.tem_imposto = tipo_ativo not in ("LCI", "LCA", "CRI", "CRA", "Poupança")
        self._valor_bruto_cache = None
        self.calcularLucro()

    def calcular_valor_bruto(self, forcar_recalculo: bool = False) -> float:
        if self._valor_bruto_cache is not None and not forcar_recalculo:
            return self._valor_bruto_cache

        hoje = date.today()
        data_ini_str = self.data_inicio.strftime("%Y-%m-%d")
        data_fim_str = hoje.strftime("%Y-%m-%d")

        if self.tipo_taxa == "IPCA":
            # 1. Busca os índices mensais do IPCA (Série 433 do SGS do BCB)
            df_ipca = sgs.get(433, start=data_ini_str, end=data_fim_str)
            
            # Acumula os meses consolidados
            if not df_ipca.empty:
                fator_ipca = float((1.0 + (df_ipca / 100.0)).prod().values[0])
            else:
                fator_ipca = 1.0

            # 2. Acumula os juros fixos anuais nos dias úteis (base 252)
            dias_uteis = np.busday_count(self.data_inicio, hoje)
            fator_pre = (1.0 + self.taxa_adicional_ipca / 100.0) ** (dias_uteis / 252.0)

            # 3. Composição geométrica
            fator_total = fator_ipca * fator_pre
            valor_bruto = self.valor_inicial * fator_total

        elif self.tipo_taxa in ("CDI", "Selic"):
            cod_serie = 12 if self.tipo_taxa == "CDI" else 11
            df = sgs.get(cod_serie, start=data_ini_str, end=data_fim_str)
            if df.empty:
                valor_bruto = self.valor_inicial
            else:
                fator_prop = self.percentual_contratado / 100.0
                fatores = 1.0 + (df / 100.0) * fator_prop
                valor_bruto = self.valor_inicial * float(fatores.prod().values[0])

        elif self.tipo_taxa == "Pré-Fixado":
            dias_uteis = np.busday_count(self.data_inicio, hoje)
            fator_total = (1.0 + self.percentual_contratado / 100.0) ** (dias_uteis / 252.0)
            valor_bruto = self.valor_inicial * fator_total

        else:
            valor_bruto = self.valor_inicial

        self._valor_bruto_cache = round(valor_bruto, 2)
        return self._valor_bruto_cache

    def calcular_impostos(self, valor_bruto: float = None):
        if valor_bruto is None:
            valor_bruto = self.calcular_valor_bruto()

        lucro_bruto = max(0.0, valor_bruto - self.valor_inicial)
        if self.data_vencimento is not None and self.data_vencimento < date.today():
            dias_corridos = (self.data_vencimento - self.data_inicio).days
        else:
            dias_corridos = (date.today() - self.data_inicio).days

        if not self.tem_imposto or lucro_bruto == 0.0:
            return {
                "iof": 0.0,
                "ir": 0.0,
                "aliquota_ir": 0.0,
                "valor_liquido": valor_bruto,
                "lucro_liquido": lucro_bruto
            }

        # 1. IOF regressivo nos primeiros 29 dias
        iof = 0.0
        if 0 <= dias_corridos < 30:
            idx = max(0, dias_corridos - 1)
            aliquota_iof = const.TABELA_IOF[min(idx, len(const.TABELA_IOF) - 1)]
            iof = lucro_bruto * aliquota_iof

        base_ir = max(0.0, lucro_bruto - iof)

        # 2. Tabela regressiva de IR
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
        lucro_liquido = max(0.0, valor_liquido - self.valor_inicial)

        return {
            "iof": round(iof, 2),
            "ir": round(ir, 2),
            "aliquota_ir": aliquota_ir * 100,
            "valor_liquido": round(valor_liquido, 2),
            "lucro_liquido": round(lucro_liquido, 2)
        }

    def calcularLucro(self):
        valor_bruto = self.calcular_valor_bruto()
        impostos = self.calcular_impostos(valor_bruto=valor_bruto)
        self.valor_liquido = impostos["valor_liquido"]
        self.lucro_liquido = impostos["lucro_liquido"]