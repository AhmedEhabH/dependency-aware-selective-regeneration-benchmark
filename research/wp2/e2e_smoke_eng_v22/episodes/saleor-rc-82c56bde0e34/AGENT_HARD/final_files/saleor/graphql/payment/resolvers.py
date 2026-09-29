from ...app import models as app_models
from ...checkout import models as checkout_models
from ...order import models as order_models
from ...payment import models
from ..account.utils import get_user_accessible_channels
from ..utils import get_user_or_app_from_context


def resolve_payment_by_id(id):
    return models.Payment.objects.filter(id=id).first()


def resolve_payments(info):
    requestor = get_user_or_app_from_context(info.context)
    payments = models.Payment.objects.all()
    if isinstance(requestor, app_models.App):
        return payments
    accessible_channels = get_user_accessible_channels(info, requestor)
    channel_ids = [channel.id for channel in accessible_channels]
    orders = order_models.Order.objects.filter(channel_id__in=channel_ids)
    return payments.filter(order_id__in=orders.values("id"))


def resolve_transaction(id):
    if id.isdigit():
        query_params = {"id": id, "use_old_id": True}
    else:
        query_params = {"token": id}
    return models.TransactionItem.objects.filter(**query_params).first()


def resolve_checkout_lines(info, checkout_id):
    """Resolve checkout lines for payment gateway."""
    checkout = checkout_models.Checkout.objects.filter(token=checkout_id).first()
    if not checkout:
        return []
    from ...checkout.fetch import fetch_checkout_lines
    from ...plugins.manager import get_plugins_manager
    
    manager = get_plugins_manager()
    lines_info, _ = fetch_checkout_lines(checkout, manager)
    return lines_info


def resolve_checkout_info(info, checkout_id):
    """Resolve checkout info for payment gateway."""
    checkout = checkout_models.Checkout.objects.filter(token=checkout_id).first()
    if not checkout:
        return None
    from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
    from ...plugins.manager import get_plugins_manager
    
    manager = get_plugins_manager()
    lines_info, _ = fetch_checkout_lines(checkout, manager)
    checkout_info = fetch_checkout_info(
        checkout=checkout,
        lines=lines_info,
        manager=manager,
    )
    return checkout_info
