from app.domain.models import Document, DocumentCategory, QueueTicket


def tpa_involved(ticket: QueueTicket) -> bool:
    return len(ticket.documents) > 0


def required_forms(ticket: QueueTicket) -> list[Document]:
    """Paper forms the nurse fills by hand (step 2.3). The remaining document
    categories are electronic forms already autofilled from prior submissions,
    handled through the existing per-document confirm flow (step 2.1)."""
    return [doc for doc in ticket.documents if doc.category is DocumentCategory.FORM]
