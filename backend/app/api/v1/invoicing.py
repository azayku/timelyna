"""Finance invoice routes — /api/v1/finance/invoices/..."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.core.module_license_deps import require_finance_license
from app.services.invoicing_service import InvoicingService

router = APIRouter(prefix="/finance/invoices", tags=["invoicing"])

_finance_or_admin = require_role("finance", "admin")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreateInvoiceRequest(BaseModel):
    client_id: int
    period: str  # "2025-03" or "2025-Q1"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: CreateInvoiceRequest,
    current_user: dict = Depends(_finance_or_admin),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = InvoicingService(db)
    return await svc.create_draft(
        client_id=body.client_id,
        period=body.period,
        created_by=current_user.get("employee_id"),
    )


@router.get("")
async def list_invoices(
    client_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(_finance_or_admin),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> list:
    svc = InvoicingService(db)
    return await svc.list_invoices(client_id=client_id, status=status, skip=skip, limit=limit)


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    current_user: dict = Depends(_finance_or_admin),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = InvoicingService(db)
    return await svc.get_by_id(invoice_id)


@router.post("/{invoice_id}/finalize")
async def finalize_invoice(
    invoice_id: int,
    current_user: dict = Depends(_finance_or_admin),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = InvoicingService(db)
    return await svc.finalize(invoice_id, performed_by=current_user.get("employee_id"))


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    current_user: dict = Depends(_finance_or_admin),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = InvoicingService(db)
    return await svc.send(invoice_id)


@router.get("/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    current_user: dict = Depends(_finance_or_admin),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
):
    """Generate and stream an HTML invoice as a downloadable file."""
    from fastapi import HTTPException
    from fastapi.responses import HTMLResponse
    svc = InvoicingService(db)
    invoice = await svc.get_by_id(invoice_id)

    if invoice["status"] not in ("sent", "ready", "paid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice must be finalized before downloading",
        )

    # Build a simple HTML invoice
    line_rows = ""
    for item in (invoice.get("line_items") or []):
        line_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee">{item['project_name']}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">{item['hours']}h</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">{item['rate']:.2f} {invoice['currency']}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:right;font-weight:bold">{item['subtotal']:.2f} {invoice['currency']}</td>
        </tr>"""

    tax = invoice.get("tax_amount") or 0
    subtotal = invoice["total_amount"] - tax

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Facture {invoice['invoice_number']}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; color: #333; }}
    h1 {{ color: #4f46e5; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th {{ background: #f3f4f6; padding: 10px 8px; text-align: left; font-size: 12px; text-transform: uppercase; }}
    .totals {{ margin-top: 20px; text-align: right; }}
    .totals td {{ padding: 4px 8px; }}
    .total-row {{ font-size: 18px; font-weight: bold; color: #4f46e5; }}
    .badge {{ display:inline-block; padding:4px 10px; border-radius:20px; font-size:12px;
              background:#d1fae5; color:#065f46; }}
    .header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:30px; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>TimesheetPro</h1>
      <p style="color:#6b7280;margin:0">Facture professionnelle</p>
    </div>
    <div style="text-align:right">
      <h2 style="margin:0">{invoice['invoice_number']}</h2>
      <p style="color:#6b7280;margin:4px 0">Période : {invoice['period']}</p>
      <span class="badge">{invoice['status'].upper()}</span>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Projet</th>
        <th style="text-align:right">Heures</th>
        <th style="text-align:right">Taux</th>
        <th style="text-align:right">Sous-total</th>
      </tr>
    </thead>
    <tbody>
      {line_rows if line_rows else '<tr><td colspan="4" style="padding:20px;text-align:center;color:#9ca3af">Aucune ligne</td></tr>'}
    </tbody>
  </table>

  <table class="totals" style="width:300px;margin-left:auto;margin-top:20px">
    <tr><td>Sous-total HT</td><td style="text-align:right">{subtotal:.2f} {invoice['currency']}</td></tr>
    <tr><td>TVA ({invoice['tax_rate']}%)</td><td style="text-align:right">{tax:.2f} {invoice['currency']}</td></tr>
    <tr class="total-row"><td><strong>Total TTC</strong></td><td style="text-align:right"><strong>{invoice['total_amount']:.2f} {invoice['currency']}</strong></td></tr>
  </table>

  <p style="margin-top:40px;color:#9ca3af;font-size:12px;text-align:center">
    Généré par TimesheetPro · {invoice['created_at'][:10]}
  </p>
</body>
</html>"""

    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f'attachment; filename="facture-{invoice["invoice_number"]}.html"',
        },
    )
