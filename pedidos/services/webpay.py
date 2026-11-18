from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys


class WebpayService:
    """
    RF02: Generar link de pago automático.
    S04: Tokenización - datos de tarjeta no pasan por nuestro servidor.
    """

    def __init__(self):
        self.tx = Transaction(
            WebpayOptions(
                IntegrationCommerceCodes.WEBPAY_PLUS,
                IntegrationApiKeys.WEBPAY,
                IntegrationType.TEST
            )
        )

    def crear_transaccion(self, pedido_id, monto, return_url):
        """Crea una transacción en Webpay Plus."""
        response = self.tx.create(
            buy_order=str(pedido_id),
            session_id=str(pedido_id),
            amount=monto,
            return_url=return_url
        )
        # SDK 6.x devuelve diccionario con 'token' y 'url'
        return {
            'token': response['token'],
            'url': response['url']
        }  # ← Llave de cierre agregada

    def confirmar_transaccion(self, token):
        """Confirma el pago tras el retorno del cliente."""
        response = self.tx.commit(token)
        # También devuelve diccionario en SDK 6.x
        return response