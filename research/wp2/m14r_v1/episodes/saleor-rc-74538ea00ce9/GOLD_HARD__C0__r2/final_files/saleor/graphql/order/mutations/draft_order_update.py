import graphene
from django.core.exceptions import ValidationError

from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .draft_order_create import DraftOrderCreate, DraftOrderInput


class DraftOrderUpdate(DraftOrderCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a draft order to update.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a draft order to update. {ADDED_IN_310}",
        )
        input = DraftOrderInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates a draft order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(
            info, qs=models.Order.objects.prefetch_related("lines"), **data
        )
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order. "
                        "Use `orderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        return instance

    @classmethod
    def should_invalidate_prices(cls, cleaned_input, *args) -> bool:
        return any(
            field in cleaned_input
            for field in [
                "shipping_address",
                "billing_address",
                "shipping_method",
                "voucher",
            ]
        )

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        
        # Handle voucher removal
        if "voucher" in cleaned_input and cleaned_input["voucher"] is None and instance.voucher:
            cls.handle_voucher_removal(instance)
        
        return cls._save_draft_order(
            info,
            instance,
            cleaned_input,
            is_new_instance=False,
            app=app,
            manager=manager,
        )

    @classmethod
    def handle_voucher_removal(cls, instance):
        """Handle voucher removal from draft order by reducing voucher usage."""
        from ....discount.utils.voucher import decrease_voucher_usage
        from ....discount.models import VoucherCode
        
        if instance.voucher_code:
            try:
                code_instance = VoucherCode.objects.get(code=instance.voucher_code)
                voucher = code_instance.voucher
                
                # Only decrease usage if the channel includes draft orders in voucher usage
                if instance.channel.include_draft_order_in_voucher_usage:
                    decrease_voucher_usage(
                        voucher,
                        code_instance,
                        instance.user_email or instance.user and instance.user.email,
                        decrease_voucher_customer_usage=False,
                    )
            except VoucherCode.DoesNotExist:
                pass
