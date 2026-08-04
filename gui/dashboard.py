"""BloodBridge dashboard built with customtkinter."""
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from __init__ import __version__

from services.donation_service import DonationService
from models.donor_model import Donor
from services.donor_service import DonorService
from services.emergency_service import EmergencyService
from services.location_data import BLOOD_GROUPS, LOCATION_TREE, URGENCY_LEVELS
from services.report_service import ReportService
from services.request_service import RequestService
from services.setup_service import SetupService
from services.stock_service import StockService
from services.validation import require_text, validate_age, validate_phone_number, validate_units


PRIMARY = "#7F1D1D"
CRIMSON = "#991B1B"
ALERT = "#B91C1C"
ACCENT = "#DC2626"
ACCENT_LIGHT = "#EF4444"
BG = "#FFF5F5"
PANEL = "#FFFFFF"
SOFT = "#FEE2E2"
TEXT = "#1F2937"
MUTED = "#6B7280"
WARNING = "#F97316"
CAUTION = "#EAB308"
SUCCESS = "#047857"
LOW_STOCK_THRESHOLD = 2
TOAST_BG = {
    "success": SUCCESS,
    "warning": WARNING,
    "error": ALERT,
    "info": PRIMARY,
}


logger = logging.getLogger(__name__)


class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("BloodBridge – Smart Emergency Blood Coordination Platform")
        self.geometry("1280x760")
        self.minsize(1120, 680)
        self.configure(fg_color=BG)
        self.active_section = "overview"
        self._refresh_after_id = None
        self._last_data_signature = None
        self._toast_windows = []
        self._table_sort_state = {}
        self.status_var = ctk.StringVar(value="Emergency network ready")
        self.last_updated_var = ctk.StringVar(value="Last Updated: --:-- --")
        self._safe_call(SetupService.ensure_emergency_schema, None)
        self._setup_table_style()
        self._build_shell()
        self.show_overview()
        self._last_data_signature = self._current_data_signature()
        self._schedule_timestamp_refresh()
        self._start_live_refresh()

    def _build_shell(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, fg_color=PRIMARY, corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(24, 24))
        ctk.CTkLabel(header, text="[blood response]", text_color=ACCENT_LIGHT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="BloodBridge",
            font=("Segoe UI", 27, "bold"),
            text_color="white",
        ).pack(anchor="w", pady=(2, 4))
        ctk.CTkLabel(
            header,
            text="Smart Emergency\nBlood Coordination Platform",
            font=("Segoe UI", 12, "bold"),
            text_color="#FECACA",
            justify="left",
        ).pack(anchor="w")
        ctk.CTkLabel(header, text=f"Version {__version__}", text_color="#FCA5A5", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8, 0))

        nav = (
            ("Dashboard", self.show_overview),
            ("Emergency Network", self.show_emergency_network),
            ("Critical Blood Requests", self.show_requests),
            ("Donation History", self.show_donation_history),
            ("Emergency Analytics", self.show_reports),
            ("Exit", self.destroy),
        )
        for label, command in nav:
            ctk.CTkButton(
                self.sidebar,
                text=label,
                command=command,
                height=46,
                corner_radius=8,
                fg_color="transparent",
                hover_color=CRIMSON,
                anchor="w",
                font=("Segoe UI", 14, "bold"),
            ).pack(fill="x", padx=14, pady=5)

        ctk.CTkLabel(
            self.sidebar,
            textvariable=self.status_var,
            text_color="#FEE2E2",
            wraplength=180,
            justify="left",
            font=("Segoe UI", 12),
        ).pack(side="bottom", fill="x", padx=18, pady=20)

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(self.main, fg_color=PANEL, height=72, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(0, weight=1)
        topbar.grid_columnconfigure(1, weight=0)
        self.page_title = ctk.CTkLabel(
            topbar,
            text="Emergency Blood Coordination Control Center",
            text_color=PRIMARY,
            font=("Segoe UI", 24, "bold"),
        )
        self.page_title.grid(row=0, column=0, sticky="w", padx=28, pady=(12, 0))
        self.page_subtitle = ctk.CTkLabel(
            topbar,
            text="Real-time donor tracking and emergency response system",
            text_color=MUTED,
            font=("Segoe UI", 12, "bold"),
        )
        self.page_subtitle.grid(row=1, column=0, sticky="w", padx=28, pady=(0, 10))
        topbar_meta = ctk.CTkFrame(topbar, fg_color="transparent")
        topbar_meta.grid(row=0, column=1, rowspan=2, sticky="e", padx=28, pady=12)
        ctk.CTkLabel(topbar_meta, textvariable=self.last_updated_var, text_color=MUTED, font=("Segoe UI", 11, "bold")).pack(anchor="e", pady=(0, 4))
        topbar_actions = ctk.CTkFrame(topbar_meta, fg_color="transparent")
        topbar_actions.pack(anchor="e")
        ctk.CTkButton(topbar_actions, text="About", width=82, command=self._show_about_dialog, fg_color=SOFT, text_color=PRIMARY, hover_color="#FBCACA", corner_radius=8, height=38).pack(side="left", padx=(0, 8))
        ctk.CTkButton(topbar_actions, text="New Emergency Request", command=self.show_requests, fg_color=ACCENT, hover_color=PRIMARY, corner_radius=8, height=38).pack(side="left")

        self.content = ctk.CTkScrollableFrame(self.main, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=22, pady=18)
        self.content.grid_columnconfigure(0, weight=1)

    def _clear(self, title):
        self.page_title.configure(text=title)
        if title == "Emergency Blood Coordination Control Center":
            self.page_subtitle.configure(text="Real-time donor tracking and emergency response system")
        else:
            self.page_subtitle.configure(text="Smart Emergency Blood Coordination Platform")
        for child in self.content.winfo_children():
            child.destroy()

    def _safe_call(self, fn, fallback):
        try:
            return fn()
        except Exception as exc:
            logger.exception("Dashboard data load failed")
            self.status_var.set(f"Database unavailable: {exc}")
            return fallback

    def _show_about_dialog(self):
        messagebox.showinfo(
            f"About BloodBridge {__version__}",
            "BloodBridge is an emergency blood coordination dashboard for donor matching, critical requests, stock monitoring, and donation history management.\n\n"
            f"Version: {__version__}\n"
            "Theme: Red medical emergency operations",
        )

    def _format_location(self, state=None, district=None, city=None):
        parts = [part for part in (state, district, city) if part]
        return " · ".join(parts) if parts else "Location unavailable"

    def _format_elapsed(self, timestamp):
        if not hasattr(timestamp, "strftime"):
            return "Unknown"
        elapsed = datetime.now() - timestamp
        total_minutes = max(0, int(elapsed.total_seconds() // 60))
        hours, minutes = divmod(total_minutes, 60)
        days, hours = divmod(hours, 24)
        if days:
            return f"{days}d {hours}h ago"
        if hours:
            return f"{hours}h {minutes}m ago"
        return f"{minutes}m ago"

    def _request_priority_label(self, priority):
        level = (priority or "").title()
        if level == "Critical":
            return "Emergency", ALERT
        if level == "High":
            return "Urgent", WARNING
        return "Normal", PRIMARY

    def _is_valid_phone(self, value):
        try:
            validate_phone_number(value)
            return True
        except Exception:
            return False

    def _setup_table_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            logger.debug("Unable to apply clam theme", exc_info=True)
        style.configure(
            "BloodBridge.Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=TEXT,
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "BloodBridge.Treeview.Heading",
            background=SOFT,
            foreground=PRIMARY,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "BloodBridge.Treeview",
            background=[("selected", "#FDE68A")],
            foreground=[("selected", TEXT)],
        )

    def _sync_last_updated(self):
        self.last_updated_var.set(f"Last Updated: {datetime.now().strftime('%I:%M %p')}")

    def _schedule_timestamp_refresh(self):
        self._sync_last_updated()
        self.after(30000, self._schedule_timestamp_refresh)

    def _show_toast(self, message, kind="info"):
        window = ctk.CTkToplevel(self)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.attributes("-alpha", 0.0)
        window.configure(fg_color=TOAST_BG.get(kind, PRIMARY))

        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() - 340
        y = self.winfo_rooty() + self.winfo_height() - 120 - (len(self._toast_windows) * 76)
        window.geometry(f"320x64+{x}+{y}")
        frame = ctk.CTkFrame(window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=14, pady=12)
        ctk.CTkLabel(frame, text=message, text_color="white", justify="left", wraplength=280, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self._toast_windows.append(window)

        def fade_in(alpha=0.0):
            if not window.winfo_exists():
                return
            window.attributes("-alpha", alpha)
            if alpha < 0.95:
                window.after(20, lambda: fade_in(alpha + 0.12))

        def dismiss():
            if window.winfo_exists():
                self._toast_windows = [toast for toast in self._toast_windows if toast is not window]
                try:
                    window.destroy()
                except Exception:
                    logger.debug("Toast window destroy failed", exc_info=True)

        fade_in()
        window.after(3200, dismiss)

    def _set_page_context(self, title, subtitle=None):
        self._clear(title)
        if subtitle:
            self.page_subtitle.configure(text=subtitle)
        self._sync_last_updated()

    def _card(self, parent, fg=PANEL):
        return ctk.CTkFrame(parent, fg_color=fg, corner_radius=16, border_width=1, border_color="#F3C6C6")

    def _badge(self, parent, text, color, width=None):
        options = {
            "text": text,
            "fg_color": color,
            "text_color": "white",
            "corner_radius": 999,
            "padx": 10,
            "pady": 4,
            "font": ("Segoe UI", 11, "bold"),
        }
        if width is not None:
            try:
                options["width"] = int(width)
            except Exception:
                options["width"] = width
        return ctk.CTkLabel(parent, **options)

    def _status_badge(self, units):
        if units > 5:
            return "SAFE", SUCCESS
        if units >= 2:
            return "LOW", WARNING
        return "CRITICAL", ALERT

    def _urgency_badge(self, urgency):
        level = (urgency or "").upper()
        if level == "CRITICAL":
            return "CRITICAL", ALERT
        if level == "HIGH":
            return "HIGH", WARNING
        return "NORMAL", PRIMARY

    def _empty_state(self, parent, title, detail):
        box = self._card(parent, fg="#FFF7ED")
        try:
            uses_grid = bool(parent.grid_slaves())
        except Exception:
            uses_grid = False
        if uses_grid:
            try:
                parent.grid_columnconfigure(0, weight=1)
            except Exception:
                logger.debug("Unable to configure empty-state grid", exc_info=True)
            box.grid(row=0, column=0, sticky="nsew", padx=8, pady=10)
        else:
            box.pack(fill="both", expand=True, padx=8, pady=10)
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=24)
        ctk.CTkLabel(inner, text="◌", text_color="#F59E0B", font=("Segoe UI", 28, "bold")).pack()
        ctk.CTkLabel(inner, text=title, text_color=PRIMARY, font=("Segoe UI", 16, "bold")).pack(pady=(10, 2))
        ctk.CTkLabel(inner, text=detail, text_color=MUTED, font=("Segoe UI", 12), justify="center", wraplength=420).pack()
        return box

    def _hover_card(self, widget, active_fg="#FEF2F2", normal_fg=None):
        normal = normal_fg or widget.cget("fg_color")

        def enter(_event):
            widget.configure(fg_color=active_fg)

        def leave(_event):
            widget.configure(fg_color=normal)

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def _table_container(self, parent, title, subtitle=None):
        card = self._card(parent)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text=title, text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, text_color=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(2, 0))
        body = tk.Frame(card, bg="#FFFFFF", highlightthickness=0)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        return card, body

    def _make_treeview(self, parent, columns, widths, sort_types=None, height=8):
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill="both", expand=True)
        tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="BloodBridge.Treeview",
            selectmode="browse",
            height=height,
        )
        y_scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        sort_types = sort_types or {}
        for column, width in zip(columns, widths):
            tree.heading(column, text=column, command=lambda col=column: self._sort_treeview(tree, col, sort_types.get(col)))
            tree.column(column, width=width, anchor="w", stretch=True)

        tree.tag_configure("even", background="#FFF7F7")
        tree.tag_configure("odd", background="#FFFFFF")
        tree.tag_configure("active", foreground=PRIMARY)
        tree.tag_configure("resolved", foreground=SUCCESS)
        tree.tag_configure("critical", foreground=ALERT)
        tree.tag_configure("high", foreground=WARNING)
        tree.tag_configure("normal", foreground=MUTED)
        return tree

    def _sort_treeview(self, tree, column, sort_type=None):
        column_index = tree["columns"].index(column)
        items = []
        for item in tree.get_children(""):
            values = list(tree.item(item, "values"))
            value = values[column_index]
            if sort_type == "int":
                try:
                    sort_value = int(str(value).split()[0])
                except Exception:
                    sort_value = 0
            elif sort_type == "datetime":
                try:
                    sort_value = datetime.strptime(str(value), "%d %b %Y, %I:%M %p")
                except Exception:
                    try:
                        sort_value = datetime.strptime(str(value), "%Y-%m-%d %H:%M")
                    except Exception:
                        sort_value = str(value)
            elif sort_type == "date":
                try:
                    sort_value = datetime.strptime(str(value), "%d %b %Y")
                except Exception:
                    sort_value = str(value)
            else:
                sort_value = str(value).lower()
            items.append((sort_value, item, values))

        reverse = self._table_sort_state.get((id(tree), column), False)
        items.sort(key=lambda entry: entry[0], reverse=reverse)
        for index, (_, item, values) in enumerate(items):
            tree.move(item, "", index)
            tree.item(item, tags=self._row_tags(values, index))
        self._table_sort_state[(id(tree), column)] = not reverse

    def _row_tags(self, values, index):
        tags = ["even" if index % 2 == 0 else "odd"]
        text = " ".join(str(value) for value in values).upper()
        if "CRITICAL" in text:
            tags.append("critical")
        elif "HIGH" in text:
            tags.append("high")
        elif "RESOLVED" in text:
            tags.append("resolved")
        elif "ACTIVE" in text:
            tags.append("active")
        else:
            tags.append("normal")
        return tags

    def _format_created_time(self, value):
        return value.strftime("%I:%M %p") if hasattr(value, "strftime") else str(value)

    def _current_data_signature(self):
        stats = self._safe_call(ReportService.dashboard_stats, {})
        alert = self._safe_call(EmergencyService.active_high_alert, None)
        pending = self._safe_call(RequestService.get_active_requests, [])
        stock = self._safe_call(StockService.get_city_stock, [])
        donors = self._safe_call(DonorService.get_all_donors, [])
        return (
            stats.get("total_donors", 0),
            stats.get("total_units", 0),
            stats.get("emergency_requests", 0),
            stats.get("critical_alerts", 0),
            stats.get("active_donors", 0),
            alert["alert_id"] if alert else None,
            alert["status"] if alert else None,
            tuple(row[0] for row in pending),
            tuple((row[1], row[2], row[3]) for row in stock),
            tuple((row[0], row[8]) for row in donors),
        )

    def _start_live_refresh(self):
        self.after(5000, self._poll_for_data_changes)

    def _poll_for_data_changes(self):
        signature = self._current_data_signature()
        if self._last_data_signature is not None and signature != self._last_data_signature:
            self._refresh_active_section(highlight=True)
        self._last_data_signature = signature
        self.after(5000, self._poll_for_data_changes)

    def _publish_data_changed(self, message=None):
        if message:
            self.status_var.set(message)
        if self._refresh_after_id:
            self.after_cancel(self._refresh_after_id)
        self._refresh_after_id = self.after(80, lambda: self._refresh_active_section(highlight=True))

    def refresh_analytics(self):
        """Public method to refresh analytics page contents and charts."""
        if self.active_section == "reports":
            try:
                self.show_reports()
            except Exception as exc:
                self._show_toast(f"Analytics refresh failed: {exc}", kind="error")

    def _refresh_active_section(self, highlight=False):
        self._refresh_after_id = None
        section = self.active_section
        if section == "overview":
            self.show_overview()
        elif section == "network":
            self.show_emergency_network()
        elif section == "requests":
            if hasattr(self, "active_request_tree") and self.active_request_tree and self.active_request_tree.winfo_exists():
                self._load_requests()
            else:
                self.show_requests()
        elif section == "donations":
            self.show_donation_history()
        elif section == "reports":
            self.show_reports()
        elif section == "matching":
            self.show_overview()
        self._last_data_signature = self._current_data_signature()
        if highlight:
            self._flash_live_update()

    def _flash_live_update(self):
        if not self.content.winfo_exists():
            return
        self.content.configure(fg_color="#FEF2F2")
        self.after(260, lambda: self.content.winfo_exists() and self.content.configure(fg_color=BG))

    def show_overview(self):
        self.active_section = "overview"
        self._set_page_context("Emergency Blood Coordination Control Center", "Real-time donor tracking and emergency response system")
        stats = self._safe_call(ReportService.dashboard_stats, {})
        alert = self._safe_call(EmergencyService.active_high_alert, None)

        self._render_alert_panel(alert)
        banner_row = 1
        if alert and alert.get("urgency_level") == "CRITICAL":
            self._render_broadcast_banner(alert)
            banner_row = 2

        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.grid(row=banner_row, column=0, sticky="ew", pady=(16, 10))
        for i in range(6):
            stats_row.grid_columnconfigure(i, weight=1)
        cards = (
            ("Total Registered Donors", stats.get("total_donors", 0)),
            ("Total Blood Units", stats.get("total_units", 0)),
            ("Emergency Requests", stats.get("emergency_requests", 0)),
            ("Critical Alerts", stats.get("critical_alerts", 0)),
            ("Available Cities", stats.get("available_cities", 0)),
            ("Active Donors", stats.get("active_donors", 0)),
        )
        for i, (label, value) in enumerate(cards):
            card = self._card(stats_row)
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            ctk.CTkLabel(card, text=label, text_color=MUTED, font=("Segoe UI", 11, "bold"), wraplength=135).pack(anchor="w", padx=12, pady=(12, 4))
            ctk.CTkLabel(card, text=str(value), text_color=PRIMARY, font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=12, pady=(0, 12))

        lower = ctk.CTkFrame(self.content, fg_color="transparent")
        lower.grid(row=banner_row + 1, column=0, sticky="ew", pady=8)
        lower.grid_columnconfigure(0, weight=3, uniform="overview_columns")
        lower.grid_columnconfigure(1, weight=2, uniform="overview_columns")
        self._render_city_map(lower)
        self._render_priority_queue(lower)

    def _render_alert_panel(self, alert):
        panel_color = ALERT if alert else "#ECFDF5"
        panel = self._card(self.content, fg=panel_color)
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(0, weight=3)
        panel.grid_columnconfigure(1, weight=1)

        if alert:
            headline = "🚨 CRITICAL ALERT"
            request_time = alert.get("request_time")
            detail = f"{alert['patient_name']} requires {alert['blood_group']} Blood"
            meta = f"{alert['hospital_name']} • {alert['city']}"
            request_text = request_time.strftime("%d %b %Y, %I:%M %p") if hasattr(request_time, "strftime") else str(request_time)
            elapsed = self._format_elapsed(request_time)
            left = ctk.CTkFrame(panel, fg_color="transparent")
            left.grid(row=0, column=0, sticky="nsew", padx=(20, 14), pady=18)
            left.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(left, text=headline, text_color="white", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(left, text=alert["patient_name"], text_color="white", font=("Segoe UI", 40, "bold"), wraplength=780, justify="left").grid(row=1, column=0, sticky="w", pady=(8, 0))
            ctk.CTkLabel(left, text=f"requires {alert['blood_group']} Blood", text_color="white", font=("Segoe UI", 24, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 8))
            ctk.CTkLabel(left, text=meta, text_color="#FDE8E8", font=("Segoe UI", 18, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 12))

            badge_row = ctk.CTkFrame(left, fg_color="transparent")
            badge_row.grid(row=4, column=0, sticky="w", pady=(0, 12))
            pr_label, pr_color = self._request_priority_label(alert.get("urgency_level"))
            self._badge(badge_row, pr_label, pr_color).pack(side="left", padx=(0, 8))
            self._badge(badge_row, alert["blood_group"], PRIMARY).pack(side="left", padx=(0, 8))
            self._badge(badge_row, f"{len(alert['matching_donors'])} Matching Donors", SUCCESS if alert["matching_donors"] else WARNING).pack(side="left", padx=(0, 8))
            self._badge(badge_row, alert["city"], ACCENT).pack(side="left", padx=(0, 8))
            self._badge(badge_row, elapsed, PRIMARY).pack(side="left")

            ctk.CTkLabel(left, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", text_color="#FDE8E8", font=("Segoe UI", 13, "bold")).grid(row=5, column=0, sticky="w", pady=(0, 10))

            units_row = ctk.CTkFrame(left, fg_color="transparent")
            units_row.grid(row=6, column=0, sticky="ew")
            units_row.grid_columnconfigure(0, weight=1)
            units_row.grid_columnconfigure(1, weight=1)

            required_block = ctk.CTkFrame(units_row, fg_color="transparent")
            required_block.grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(required_block, text="Required Units", text_color="#FECACA", font=("Segoe UI", 18, "bold")).pack(anchor="w")
            ctk.CTkLabel(required_block, text=str(alert["required_units"]), text_color="white", font=("Segoe UI", 34, "bold")).pack(anchor="w", pady=(2, 0))

            available_block = ctk.CTkFrame(units_row, fg_color="transparent")
            available_block.grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(available_block, text="Available Units", text_color="#FECACA", font=("Segoe UI", 18, "bold")).pack(anchor="w")
            ctk.CTkLabel(available_block, text=str(alert["available_units"]), text_color="white", font=("Segoe UI", 34, "bold")).pack(anchor="w", pady=(2, 0))

            ctk.CTkLabel(left, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", text_color="#FDE8E8", font=("Segoe UI", 13, "bold")).grid(row=7, column=0, sticky="w", pady=(12, 0))

            right = ctk.CTkFrame(panel, fg_color="transparent")
            right.grid(row=0, column=1, sticky="nsew", padx=(12, 20), pady=18)
            right.grid_rowconfigure(0, weight=1)
            right.grid_columnconfigure(0, weight=1)
            ctk.CTkButton(right, text="View Matching Donors", command=lambda: self.show_matching_donors(alert), fg_color=PRIMARY, corner_radius=8, height=44).grid(row=0, column=0, sticky="ew", pady=(0, 10))
            ctk.CTkButton(right, text="Contact Donors", command=lambda: self.show_matching_donors(alert), fg_color=ACCENT, corner_radius=8, height=44).grid(row=1, column=0, sticky="ew", pady=(0, 10))
            ctk.CTkButton(right, text="Mark Blood Arranged", command=lambda aid=alert["alert_id"]: self._fulfill_alert(aid), fg_color=SUCCESS, corner_radius=8, height=44).grid(row=2, column=0, sticky="ew")
            self._pulse_alert(panel, True)
        else:
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=16)
            self._badge(row, "NORMAL", SUCCESS).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(row, text="No active emergencies", text_color=SUCCESS, font=("Segoe UI", 22, "bold")).pack(side="left")
            ctk.CTkLabel(panel, text="Coordinator network is standing by for the next critical alert.", text_color=MUTED, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=20, pady=(0, 16))

    def _render_broadcast_banner(self, alert):
        banner = self._card(self.content, fg="#7F1D1D")
        banner.grid(row=1, column=0, sticky="ew", pady=(14, 6))
        banner.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            banner,
            text=f"🚨 Broadcasting urgent {alert['blood_group']} blood requirement in {alert['city']}...",
            text_color="white",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(12, 2))
        ctk.CTkLabel(
            banner,
            text=f"Coordinator notifications sent. Matching donors identified. {len(alert['matching_donors'])} donor candidates queued.",
            text_color="#FDE8E8",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

    def _pulse_alert(self, panel, red=True):
        if not panel.winfo_exists():
            return
        panel.configure(fg_color=ALERT if red else PRIMARY)
        self.after(750, lambda: self._pulse_alert(panel, not red))

    def _render_city_map(self, parent):
        section = self._card(parent)
        section.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text="City-Wise Blood Availability", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(side="left")
        self._sync_last_updated()
        ctk.CTkLabel(header, textvariable=self.last_updated_var, text_color=MUTED, font=("Segoe UI", 11, "bold")).pack(side="right")

        rows = self._safe_call(StockService.get_city_stock, [])
        by_city = {}
        for _, city, group, units in rows:
            by_city.setdefault(city, []).append((group, units))

        if not by_city:
            self._empty_state(section, "No city stock data", "No city blood stock records are available yet.")
            return

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1, uniform="city_cards")
        for i, (city, stocks) in enumerate(by_city.items()):
            total_units = sum(units for _, units in stocks)
            overall_label, overall_color = self._status_badge(total_units // max(len(stocks), 1))
            card = ctk.CTkFrame(grid, fg_color="#FFF8F8", corner_radius=16, border_width=1, border_color="#FAD4D4")
            card.grid(row=i // 2, column=i % 2, sticky="ew", padx=8, pady=8)
            self._hover_card(card, active_fg="#FFF1F1", normal_fg="#FFF8F8")
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(12, 8))
            ctk.CTkLabel(top, text=city, text_color=TEXT, font=("Segoe UI", 18, "bold")).pack(side="left")
            self._badge(top, overall_label, overall_color).pack(side="right")

            summary = ctk.CTkFrame(card, fg_color="transparent")
            summary.pack(fill="x", padx=14, pady=(0, 10))
            ctk.CTkLabel(summary, text=f"Total stock: {total_units} units", text_color=PRIMARY, font=("Segoe UI", 12, "bold")).pack(anchor="w")
            pill_row = ctk.CTkFrame(card, fg_color="transparent")
            pill_row.pack(fill="x", padx=12, pady=(0, 12))
            for badge_col in range(2):
                pill_row.grid_columnconfigure(badge_col, weight=1)
            for index, (group, units) in enumerate(stocks):
                label, color = self._status_badge(units)
                self._badge(pill_row, f"{group}  {units}  {label}", color).grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="ew",
                    padx=4,
                    pady=4,
                )

    def _render_priority_queue(self, parent):
        section = self._card(parent)
        section.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text="Priority Request Queue", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(side="left")
        ctk.CTkLabel(header, textvariable=self.last_updated_var, text_color=MUTED, font=("Segoe UI", 11, "bold")).pack(side="right")
        rows = self._safe_call(RequestService.get_active_requests, [])
        if not rows:
            self._empty_state(section, "No active emergencies", "Incoming critical blood requests will appear here.")
            return
        for row in rows[:7]:
            rid, patient, group, units, hospital, city, district, state, req_date, created_time, status, priority, contact_number = row
            item = ctk.CTkFrame(section, fg_color="#FFF7F7" if priority == "Critical" else "#FFF7ED" if priority == "High" else "#F8FAFC", corner_radius=16, border_width=1, border_color="#F3D1D1")
            item.pack(fill="x", padx=12, pady=6)
            self._hover_card(item, active_fg="#FEF2F2", normal_fg=item.cget("fg_color"))
            top = ctk.CTkFrame(item, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 0))
            ctk.CTkLabel(top, text=f"🚨 {patient}", text_color=TEXT, font=("Segoe UI", 15, "bold")).pack(side="left")
            urgency_label, urgency_color = self._urgency_badge(priority)
            self._badge(top, urgency_label, urgency_color).pack(side="right")
            self._badge(top, group, ALERT).pack(side="right", padx=(0, 8))
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(fill="x", padx=12, pady=(6, 4))
            ctk.CTkLabel(
                info,
                text=f"Blood Group: {group}   |   Units Required: {units}   |   Hospital: {hospital}",
                text_color=MUTED,
                font=("Segoe UI", 12, "bold"),
                justify="left",
                wraplength=440,
            ).pack(anchor="w", fill="x")
            ctk.CTkLabel(
                info,
                text=f"State: {state}   |   District: {district}   |   City / Place: {city}",
                text_color=MUTED,
                font=("Segoe UI", 12),
                justify="left",
                wraplength=440,
            ).pack(anchor="w", fill="x", pady=(2, 0))
            ctk.CTkLabel(
                info,
                text=f"Contact: {contact_number}   |   Created: {self._format_created_time(created_time)}   |   Time Elapsed: {self._format_elapsed(created_time)}",
                text_color=MUTED,
                font=("Segoe UI", 12),
                justify="left",
                wraplength=440,
            ).pack(anchor="w", fill="x", pady=(2, 0))
            actions = ctk.CTkFrame(item, fg_color="transparent")
            actions.pack(anchor="e", padx=12, pady=(4, 10))
            ctk.CTkButton(actions, text="Mark Resolved", width=120, fg_color=SUCCESS, corner_radius=6, command=lambda r=rid: self._resolve_request(r)).pack(side="left", padx=4)
            ctk.CTkButton(actions, text="View Matching Donors", width=150, fg_color=WARNING, corner_radius=6, command=lambda p=patient, g=group, c=city, d=district, s=state, h=hospital, u=units, cn=contact_number: self.show_matching_donors({"patient_name": p, "blood_group": g, "city": c, "district": d, "state": s, "hospital_name": h, "required_units": u, "request_contact": cn, "matching_donors": DonorService.find_matching_donors(g, c)})).pack(side="left", padx=4)
            ctk.CTkButton(actions, text="Contact Requester", width=140, fg_color=PRIMARY, corner_radius=6, command=lambda c=contact_number: self._contact_requester(c)).pack(side="left", padx=4)

    def show_matching_donors(self, alert):
        self.active_section = "matching"
        location = self._format_location(alert.get("state"), alert.get("district"), alert.get("city"))
        self._set_page_context(f"Matching Donors - {alert['blood_group']} in {alert['city']}", f"Exact and compatible matches prioritized by location and availability | {location}")
        requester = alert.get("request_contact")
        if requester:
            bar = self._card(self.content, fg=SOFT)
            bar.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                bar,
                text=f"Emergency Contact: {requester}",
                text_color=PRIMARY,
                font=("Segoe UI", 14, "bold"),
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkButton(
                bar,
                text="Contact Requester",
                fg_color=PRIMARY,
                corner_radius=6,
                command=lambda c=requester: self._contact_requester(c),
            ).pack(side="right", padx=12, pady=8)
        self._donor_cards(alert["matching_donors"], compact=True, target_city=alert.get("city"), target_group=alert.get("blood_group"))

    def show_emergency_network(self):
        self.active_section = "network"
        self._set_page_context("Emergency Donor Network", "Search donors, update status, and coordinate contact actions in real time")
        search = self._card(self.content)
        search.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for i in range(7):
            search.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(search, text="Smart Search", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        location = self._location_selectors(search, row=1, start_col=0)
        blood_group = self._menu(search, ["Any"] + BLOOD_GROUPS, "Any")
        blood_group.grid(row=1, column=3, padx=8, pady=(12, 8), sticky="ew")
        donor_name = ctk.CTkEntry(search, placeholder_text="Donor name")
        donor_name.grid(row=1, column=4, padx=8, pady=(12, 8), sticky="ew")
        availability = self._menu(search, ["Any", "Available", "Recently Donated", "Inactive"], "Any")
        availability.grid(row=1, column=5, padx=8, pady=(12, 8), sticky="ew")
        ctk.CTkButton(
            search,
            text="Search Network",
            command=lambda: self._load_network_results(location, blood_group, donor_name, availability),
            fg_color=PRIMARY,
            corner_radius=6,
        ).grid(row=1, column=6, padx=8, pady=(12, 8), sticky="ew")

        add = self._card(self.content)
        add.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for i in range(6):
            add.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(add, text="Register Donor", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        row1 = ctk.CTkFrame(add, fg_color="transparent")
        row1.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10)
        for i in range(4):
            row1.grid_columnconfigure(i, weight=1)
        fields = self._build_inputs(row1, ("Name", "Age", "Gender", "Contact"), row=0)

        row2 = ctk.CTkFrame(add, fg_color="transparent")
        row2.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10)
        for i in range(5):
            row2.grid_columnconfigure(i, weight=1)
        add_bg = self._menu(row2, BLOOD_GROUPS, BLOOD_GROUPS[0])
        add_bg.grid(row=0, column=0, padx=8, pady=(4, 6), sticky="ew")
        add_location = self._location_selectors(row2, row=0, start_col=1)
        add_status = self._menu(row2, ["Available", "Recently Donated", "Inactive"], "Available", width=160)
        add_status.grid(row=0, column=4, padx=8, pady=(4, 6), sticky="ew")

        row3 = ctk.CTkFrame(add, fg_color="transparent")
        row3.grid(row=3, column=0, columnspan=6, sticky="ew", padx=10, pady=(0, 12))
        row3.grid_columnconfigure(0, weight=1)
        row3.grid_columnconfigure(1, weight=0)
        row3.grid_columnconfigure(2, weight=1)
        ctk.CTkButton(
            row3,
            text="Add Donor",
            command=lambda: self._add_donor(fields, add_bg.get(), add_location, add_status.get()),
            fg_color=CRIMSON,
            corner_radius=6,
            height=40,
        ).grid(row=0, column=1, sticky="ew")

        split = ctk.CTkFrame(self.content, fg_color="transparent")
        split.grid(row=2, column=0, sticky="ew")
        split.grid_columnconfigure(0, weight=2)
        split.grid_columnconfigure(1, weight=1)

        donors_section = self._card(split)
        donors_section.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(donors_section, text="Matching Donors", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        self.network_donor_list = ctk.CTkFrame(donors_section, fg_color="transparent")
        self.network_donor_list.pack(fill="x", padx=12, pady=(0, 12))

        right = ctk.CTkFrame(split, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.network_matching = self._card(right)
        self.network_matching.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(self.network_matching, text="Emergency Matching", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        self.network_alerts = self._card(right)
        self.network_alerts.pack(fill="x")
        ctk.CTkLabel(self.network_alerts, text="Critical Alerts", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(12, 4))

        stock_section = self._card(self.content)
        stock_section.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        header = ctk.CTkFrame(stock_section, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(header, text="City Blood Stock", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(side="left")
        ctk.CTkLabel(header, textvariable=self.last_updated_var, text_color=MUTED, font=("Segoe UI", 11, "bold")).pack(side="right")
        self.network_stock_list = ctk.CTkFrame(stock_section, fg_color="transparent")
        self.network_stock_list.pack(fill="x", padx=12, pady=(0, 12))

        self._show_network_idle(location["City"].get())

    def _show_network_idle(self, city):
        requests = self._safe_call(RequestService.get_active_requests, [])
        active = [row for row in requests if row[5] == city]
        if active:
            _, _, group, _, _, _, _, _, _, _, _, _, _ = active[0]
            donors = self._safe_call(lambda: DonorService.find_matching_donors(group, city), [])
            self._donor_cards(donors, compact=True, parent=self.network_donor_list, target_city=city, target_group=group)
            self._render_network_matching(city, group, donors)
        else:
            self._empty_state(self.network_donor_list, "No matching donors yet", "Search donors or create an emergency request to see recommendations.")
            self._empty_state(self.network_matching, "No active emergency request", "Emergency matching appears when an active request exists.")
        self._render_network_alerts(city)
        self._render_network_stock(city)

    def _load_network_results(self, location, blood_group, donor_name, availability):
        city = location["City"].get()
        group = None if blood_group.get() == "Any" else blood_group.get()
        status = None if availability.get() == "Any" else availability.get()
        name = donor_name.get().strip() or None

        for container in (self.network_donor_list, self.network_stock_list, self.network_matching, self.network_alerts):
            for child in container.winfo_children()[1:] if container in (self.network_matching, self.network_alerts) else container.winfo_children():
                child.destroy()

        donors = self._safe_call(lambda: DonorService.search_donors(name=name, blood_group=group, city=city, status=status), [])
        self._donor_cards(donors, parent=self.network_donor_list, target_city=city, target_group=group)
        self._render_network_stock(city)
        self._render_network_matching(city, group, donors)
        self._render_network_alerts(city)

    def _render_network_stock(self, selected_city):
        rows = self._safe_call(lambda: StockService.get_city_stock(selected_city), [])
        if not rows:
            self._empty_state(self.network_stock_list, "No city stock found", "No city stock found for this location.")
            return
        by_city = {}
        for _, city, group, units in rows:
            by_city.setdefault(city, []).append((group, units))
        for city, stocks in by_city.items():
            card = ctk.CTkFrame(self.network_stock_list, fg_color="#FFF8F8", corner_radius=14, border_width=1, border_color="#FAD4D4")
            card.pack(fill="x", pady=6)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 4))
            total_units = sum(units for _, units in stocks)
            stock_label, stock_color = self._status_badge(total_units // max(len(stocks), 1))
            ctk.CTkLabel(top, text=city, text_color=TEXT, font=("Segoe UI", 15, "bold")).pack(side="left")
            self._badge(top, stock_label, stock_color).pack(side="right")
            line = ctk.CTkFrame(card, fg_color="transparent")
            line.pack(fill="x", padx=10, pady=(0, 10))
            for group, units in stocks:
                label, color = self._status_badge(units)
                self._badge(line, f"{group}  {units}  {label}", color).pack(side="left", padx=3, pady=3)

    def _render_network_matching(self, city, blood_group, donors):
        requests = self._safe_call(RequestService.get_active_requests, [])
        urgent = [row for row in requests if row[5] == city and (not blood_group or row[2] == blood_group)]
        if urgent:
            rid, patient, group, units, hospital, city, district, state, req_date, created_time, status, priority, contact_number = urgent[0]
            matches = DonorService.find_matching_donors(group, city)
            self._simple_result(
                self.network_matching,
                f"{patient} needs {group}",
                f"{hospital}, {self._format_location(state, district, city)} | Priority: {priority} | Contact: {contact_number} | Suggested same-city donors: {len(matches)}",
                priority,
            )
            for match in matches[:3]:
                _, name, phone, group, match_city, match_district, match_state, last_date, status, match_type = match
                color = SUCCESS if status == "Available" else WARNING
                self._badge(self.network_matching, f"{match_type} · {name} · {status} · {self._format_location(match_state, match_district, match_city)}", color).pack(anchor="w", padx=12, pady=3)
                action_row = ctk.CTkFrame(self.network_matching, fg_color="transparent")
                action_row.pack(anchor="w", padx=12, pady=(0, 4))
                ctk.CTkButton(action_row, text="Call Donor", width=96, fg_color=PRIMARY, corner_radius=6, command=lambda p=phone: self._call_donor(p)).pack(side="left", padx=(0, 6))
                ctk.CTkButton(action_row, text="Copy Number", width=108, fg_color=WARNING, corner_radius=6, command=lambda p=phone: self._copy_number(p)).pack(side="left")
            ctk.CTkButton(
                self.network_matching,
                text=f"Contact Requester: {contact_number}",
                fg_color=PRIMARY,
                corner_radius=6,
                command=lambda c=contact_number: self._contact_requester(c),
            ).pack(anchor="w", padx=12, pady=(6, 4))
        elif blood_group:
            self._empty_state(self.network_matching, "No matching emergency", "No active emergency request for this blood group.")
        else:
            self._empty_state(self.network_matching, "Matching appears here", "Emergency matching appears when an active request exists.")

    def _render_network_alerts(self, city):
        alerts = self._safe_call(lambda: [row for row in EmergencyService.get_alerts(status="OPEN") if row[3] == city], [])
        if not alerts:
            self._empty_state(self.network_alerts, "No active alerts", "No critical alerts currently exist for this city.")
            return
        for _, patient, group, city, district, state, hospital, urgency, units, request_time, status, request_id in alerts:
            available = StockService.get_units_for_city(city, group)
            self._simple_result(
                self.network_alerts,
                f"{urgency} alert: {group} in {city}",
                f"{patient} at {hospital} | {self._format_location(state, district, city)} | Required: {units} | Available: {available} | {status}",
                urgency,
            )

    def _build_inputs(self, parent, labels, row=0):
        fields = {}
        for i, label in enumerate(labels):
            ent = ctk.CTkEntry(parent, placeholder_text=label)
            ent.grid(row=row, column=i, sticky="ew", padx=8, pady=(12, 8))
            fields[label] = ent
        return fields

    def _menu(self, parent, values, default=None, width=150):
        menu = ctk.CTkOptionMenu(parent, values=values, width=width)
        menu.set(default or values[0])
        return menu

    def _location_selectors(self, parent, row=0, start_col=0):
        state = self._menu(parent, list(LOCATION_TREE.keys()), "Karnataka")
        district = self._menu(parent, list(LOCATION_TREE["Karnataka"].keys()), "Mysuru")
        city = self._menu(parent, LOCATION_TREE["Karnataka"]["Mysuru"], "Mysore")

        def update_districts(selected_state):
            districts = list(LOCATION_TREE[selected_state].keys())
            district.configure(values=districts)
            district.set(districts[0])
            update_cities(districts[0])

        def update_cities(selected_district):
            cities = LOCATION_TREE[state.get()][selected_district]
            city.configure(values=cities)
            city.set(cities[0])

        state.configure(command=update_districts)
        district.configure(command=update_cities)
        for offset, widget in enumerate((state, district, city)):
            widget.grid(row=row, column=start_col + offset, sticky="ew", padx=8, pady=(12, 8))
        return {"State": state, "District": district, "City": city}

    def _add_donor(self, fields, blood_group, location, status):
        try:
            name = require_text(fields["Name"].get(), "donor name")
            gender = require_text(fields["Gender"].get(), "gender") or "Other"
            contact_number = validate_phone_number(fields["Contact"].get())
            if gender not in ("Male", "Female", "Other"):
                raise ValueError("invalid gender")
            donor = Donor(
                full_name=name,
                age=validate_age(fields["Age"].get(), minimum=18, maximum=65),
                gender=gender,
                blood_group=blood_group,
                city=location["City"].get(),
                district=location["District"].get(),
                state=location["State"].get(),
                availability_status=status,
                contact_number=contact_number,
            )
        except Exception:
            self.status_var.set("Enter a valid donor name, age 18-65, gender, and phone number.")
            return
        if DonorService.add_donor(donor):
            self._show_toast(f"Donor added: {donor.full_name}", "success")
            self._publish_data_changed(f"Added donor {donor.full_name}")
        else:
            self.status_var.set("Could not add donor. Check duplicate contact or database connection.")

    def _donor_cards(self, rows, compact=False, parent=None, target_city=None, target_group=None):
        parent = parent or self.content
        if not rows:
            self._empty_state(parent, "No matching donors found", "No matching donors found.")
            return
        for row in rows:
            if compact:
                _, name, phone, group, city, district, state, last_date, status, match_type = row
                donor_id = None
                age = email = ""
            else:
                donor_id, name, age, gender, group, city, district, state, status, phone, email, last_date = row
            card = self._card(parent)
            card.pack(fill="x", pady=6)
            card.grid_columnconfigure(0, weight=1)
            self._hover_card(card, active_fg="#FEF2F2", normal_fg=card.cget("fg_color"))
            title = ctk.CTkFrame(card, fg_color="transparent")
            title.grid(row=0, column=0, columnspan=4, sticky="ew", padx=14, pady=(10, 0))
            ctk.CTkLabel(title, text=name, text_color=TEXT, font=("Segoe UI", 16, "bold")).pack(side="left")
            self._badge(title, group, ALERT).pack(side="left", padx=8)
            if target_group and group == target_group:
                self._badge(title, "Compatible", SUCCESS).pack(side="left")
            if target_city and city == target_city:
                self._badge(title, "Nearest", PRIMARY).pack(side="left", padx=6)
            if compact:
                self._badge(title, match_type, SUCCESS if match_type == "Exact Match" else WARNING).pack(side="left")
            if compact:
                self._badge(title, status, SUCCESS if status == "Available" else WARNING if status == "Recently Donated" else MUTED).pack(side="left", padx=8)
            else:
                status_menu = self._menu(card, ["Available", "Recently Donated", "Inactive"], status, width=160)
                status_menu.grid(row=0, column=2, padx=8, pady=(10, 0), sticky="e")
                ctk.CTkButton(
                    card,
                    text="Update Status",
                    width=120,
                    fg_color=PRIMARY,
                    corner_radius=6,
                    command=lambda did=donor_id, menu=status_menu: self._update_donor_status(did, menu.get()),
                ).grid(row=0, column=3, padx=14, pady=(10, 0))
            action_row = ctk.CTkFrame(card, fg_color="transparent")
            action_row.grid(row=1, column=0, columnspan=4, sticky="w", padx=14, pady=(4, 0))
            ctk.CTkButton(action_row, text="Call Donor", width=96, fg_color=PRIMARY, corner_radius=6, command=lambda p=phone: self._call_donor(p)).pack(side="left", padx=(0, 6))
            ctk.CTkButton(action_row, text="Copy Number", width=108, fg_color=WARNING, corner_radius=6, command=lambda p=phone: self._copy_number(p)).pack(side="left")
            detail = f"{self._format_location(state, district, city)} | Contact: {phone} | Last Donation: {last_date or 'No record'}"
            if age:
                detail = f"Age {age} | " + detail
            if compact:
                detail = f"Availability: {status} | " + detail
            ctk.CTkLabel(card, text=detail, text_color=MUTED, font=("Segoe UI", 12)).grid(row=2, column=0, columnspan=4, sticky="w", padx=14, pady=(2, 10))

    def _update_donor_status(self, donor_id, status):
        if DonorService.update_donor(donor_id, availability_status=status):
            self._show_toast(f"Donor status updated: {status}", "success")
            self._publish_data_changed(f"Donor status changed to {status}.")
        else:
            self.status_var.set("Could not update donor status.")

    def show_requests(self):
        self.active_section = "requests"
        self._set_page_context("Emergency Requests", "Create, resolve, and coordinate active blood emergencies from one control surface")

        form = self._card(self.content)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for i in range(6):
            form.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(form, text="Create Emergency Request", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10)
        for i in range(4):
            row1.grid_columnconfigure(i, weight=1)
        fields = self._build_inputs(row1, ("Patient", "Units", "Hospital", "Emergency Contact"), row=0)

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10)
        for i in range(5):
            row2.grid_columnconfigure(i, weight=1)
        blood_group = self._menu(row2, BLOOD_GROUPS, BLOOD_GROUPS[0])
        blood_group.grid(row=0, column=0, padx=8, pady=(4, 6), sticky="ew")
        location = self._location_selectors(row2, row=0, start_col=1)
        urgency = self._menu(row2, URGENCY_LEVELS, "Critical", width=140)
        urgency.grid(row=0, column=4, padx=8, pady=(4, 6), sticky="ew")

        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.grid(row=3, column=0, columnspan=6, sticky="ew", padx=10, pady=(0, 12))
        row3.grid_columnconfigure(0, weight=1)
        row3.grid_columnconfigure(1, weight=0)
        row3.grid_columnconfigure(2, weight=1)
        ctk.CTkButton(
            row3,
            text="Create Emergency Request",
            command=lambda: self._create_request(fields, blood_group.get(), location, urgency.get()),
            fg_color=ALERT,
            corner_radius=6,
            height=40,
        ).grid(row=0, column=1, sticky="ew")

        self.request_spotlight = ctk.CTkFrame(self.content, fg_color="transparent")
        self.request_spotlight.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        active_card = self._card(self.content)
        active_card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self.active_table_host = active_card
        self.active_request_tree = None

        resolved_card = self._card(self.content)
        resolved_card.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        self.resolved_table_host = resolved_card
        self.resolved_request_tree = None

        self._load_requests()

    def _create_request(self, fields, blood_group, location, priority):
        try:
            patient = require_text(fields["Patient"].get(), "patient name")
            units = validate_units(fields["Units"].get(), minimum=1, maximum=20)
            hospital = require_text(fields["Hospital"].get(), "hospital name")
            city = location["City"].get()
            contact_number = validate_phone_number(fields["Emergency Contact"].get())
        except Exception:
            self.status_var.set("Enter patient, 1-20 units, hospital, and a valid emergency contact.")
            return
        result = RequestService.create_emergency_request(
            patient,
            blood_group,
            units,
            hospital,
            city,
            priority,
            contact_number,
            location["District"].get(),
            location["State"].get(),
        )
        if not result:
            self.status_var.set("Could not create request.")
            return
        elif result["stock_shortage"]:
            message = (
                f"Emergency request created. Alert #{result['alert_id']} raised: {units} needed, {result['available_units']} available in {city}."
            )
        else:
            message = (
                f"Emergency request created. City stock can cover it: {result['available_units']} units available in {city}."
            )
        self._show_toast(message, "warning" if result["stock_shortage"] else "success")
        self._publish_data_changed(message)

    def _load_requests(self):
        self._render_request_views()

    def _render_request_views(self):
        for child in self.request_spotlight.winfo_children():
            child.destroy()
        for child in self.active_table_host.winfo_children():
            child.destroy()
        for child in self.resolved_table_host.winfo_children():
            child.destroy()

        active_rows = self._safe_call(RequestService.get_active_requests, [])
        resolved_rows = self._safe_call(RequestService.get_resolved_requests, [])

        spotlight = self._card(self.request_spotlight)
        spotlight.pack(fill="x")
        top = ctk.CTkFrame(spotlight, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(top, text="Critical Request Spotlight", text_color=PRIMARY, font=("Segoe UI", 18, "bold")).pack(side="left")
        ctk.CTkLabel(top, text="Live priority view", text_color=MUTED, font=("Segoe UI", 11, "bold")).pack(side="right")
        self._render_request_cards(spotlight, active_rows[:4])

        active_card, active_body = self._table_container(self.active_table_host, "Active Requests", "Structured queue of unresolved blood requests")
        active_card.pack(fill="x", expand=True)
        active_tree = self._make_treeview(
            active_body,
            ["Request ID", "Patient Name", "Blood Group", "Hospital", "State", "District", "City / Place", "Units Required", "Matching Donors", "Urgency", "Status", "Contact Number", "Created Time"],
            [90, 150, 90, 160, 120, 120, 130, 110, 120, 90, 90, 130, 150],
            sort_types={"Request ID": "int", "Units Required": "int", "Matching Donors": "int", "Created Time": "datetime"},
            height=7,
        )
        self._populate_request_tree(active_tree, active_rows)
        self.active_request_tree = active_tree

        resolved_card, resolved_body = self._table_container(self.resolved_table_host, "Resolved Requests", "Completed requests automatically move into the historical log")
        resolved_card.pack(fill="x", expand=True)
        resolved_tree = self._make_treeview(
            resolved_body,
            ["Request ID", "Patient Name", "Blood Group", "Hospital", "State", "District", "City / Place", "Units Required", "Matching Donors", "Urgency", "Status", "Contact Number", "Created Time"],
            [90, 150, 90, 160, 120, 120, 130, 110, 120, 90, 90, 130, 150],
            sort_types={"Request ID": "int", "Units Required": "int", "Matching Donors": "int", "Created Time": "datetime"},
            height=6,
        )
        self._populate_request_tree(resolved_tree, resolved_rows)
        self.resolved_request_tree = resolved_tree

        if not active_rows:
            self._empty_state(self.request_spotlight, "No active emergencies", "No active requests right now. New emergencies will appear here.")

    def _render_request_cards(self, parent, rows):
        if not rows:
            return
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)
        for index, row in enumerate(rows):
            rid, patient, group, units, hospital, city, district, state, req_date, created_time, status, priority, contact_number = row
            card = ctk.CTkFrame(grid, fg_color="#FFF7F7" if priority == "Critical" else "#FFF7ED" if priority == "High" else "#F8FAFC", corner_radius=16, border_width=1, border_color="#F5C2C7")
            card.grid(row=index // 2, column=index % 2, sticky="ew", padx=6, pady=6)
            self._hover_card(card, active_fg="#FEF2F2", normal_fg=card.cget("fg_color"))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 4))
            ctk.CTkLabel(top, text=f"🚨 {patient}", text_color=TEXT, font=("Segoe UI", 15, "bold")).pack(side="left")
            urg_label, urg_color = self._urgency_badge(priority)
            self._badge(top, urg_label, urg_color).pack(side="right")
            match_count = len(DonorService.find_matching_donors(group, city))
            self._badge(top, f"{match_count} donors", SUCCESS if match_count else WARNING).pack(side="right", padx=(0, 8))
            self._badge(card, group, ALERT).pack(anchor="w", padx=12, pady=(0, 6))
            ctk.CTkLabel(card, text=f"{units} units · {hospital}", text_color=PRIMARY, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(card, text=self._format_location(state, district, city), text_color=MUTED, font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(2, 0))
            ctk.CTkLabel(card, text=f"Contact: {contact_number} · Status: {status} · Created: {self._format_created_time(created_time)} · Elapsed: {self._format_elapsed(created_time)}", text_color=MUTED, font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(2, 8))
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=12, pady=(0, 12))
            ctk.CTkButton(actions, text="Mark Resolved", width=110, fg_color=SUCCESS, corner_radius=6, command=lambda r=rid: self._resolve_request(r)).pack(side="left", padx=(0, 6))
            ctk.CTkButton(actions, text="View Matching Donors", width=145, fg_color=WARNING, corner_radius=6, command=lambda p=patient, g=group, c=city, d=district, s=state, h=hospital, u=units, cn=contact_number: self.show_matching_donors({"patient_name": p, "blood_group": g, "city": c, "district": d, "state": s, "hospital_name": h, "required_units": u, "request_contact": cn, "matching_donors": DonorService.find_matching_donors(g, c)})).pack(side="left", padx=(0, 6))
            ctk.CTkButton(actions, text="Contact Requester", width=130, fg_color=PRIMARY, corner_radius=6, command=lambda c=contact_number: self._contact_requester(c)).pack(side="left")

    def _populate_request_tree(self, tree, rows):
        if not rows:
            self._empty_state(tree.master, "No requests", "No requests are available in this section.")
            return
        for index, row in enumerate(rows):
            rid, patient, group, units, hospital, city, district, state, request_date, created_time, status, priority, contact_number = row
            created_text = created_time.strftime("%d %b %Y, %I:%M %p") if hasattr(created_time, "strftime") else str(created_time)
            match_count = len(DonorService.find_matching_donors(group, city))
            values = (rid, patient, group, hospital, state, district, city, units, match_count, priority, status, contact_number, created_text)
            tree.insert("", "end", values=values, tags=self._row_tags(values, index))
        for item in tree.get_children(""):
            tags = list(tree.item(item, "tags"))
            values = tree.item(item, "values")
            if str(values[10]).upper() == "RESOLVED":
                tags = [tag for tag in tags if tag not in ("active", "critical", "high", "normal")]
                tags.append("resolved")
            tree.item(item, tags=tags)

    def _resolve_request(self, request_id):
        if RequestService.resolve_request(request_id):
            self._show_toast("Emergency request marked resolved", "success")
            self._publish_data_changed("Emergency request marked resolved.")
        else:
            self.status_var.set("Could not mark request as resolved.")

    def _contact_requester(self, contact_number):
        self.clipboard_clear()
        self.clipboard_append(contact_number)
        self._show_toast(f"Requester contact copied: {contact_number}", "info")
        self.status_var.set(f"Requester contact copied: {contact_number}")

    def _copy_number(self, phone):
        self.clipboard_clear()
        self.clipboard_append(phone)
        self._show_toast(f"Copied number: {phone}", "info")

    def _call_donor(self, phone):
        self._show_toast(f"Calling donor: {phone}", "info")

    def _fulfill_alert(self, alert_id):
        if EmergencyService.mark_alert_fulfilled(alert_id):
            self._show_toast("Emergency alert closed after blood was arranged", "success")
            self._publish_data_changed("Emergency alert closed after blood was arranged.")
        else:
            self.status_var.set("Could not close emergency alert.")

    def _simple_result(self, parent, title, detail, badge):
        card = self._card(parent)
        card.pack(fill="x", pady=5)
        ctk.CTkLabel(card, text=title, text_color=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(card, text=detail, text_color=MUTED, font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(0, 10))

    def show_donation_history(self):
        self.active_section = "donations"
        self._set_page_context("Donation History", "Structured donation history with donor, blood group, city, and unit tracking")
        panel, body = self._table_container(self.content, "Donation History", "Verified donation records from the live database")
        panel.grid(row=0, column=0, sticky="ew")
        rows = self._safe_call(DonationService.get_history, [])
        table = self._make_treeview(
            body,
            ["Donation ID", "Donor Name", "Blood Group", "City", "Units Donated", "Donation Date"],
            [100, 200, 110, 150, 120, 150],
            sort_types={"Donation ID": "int", "Units Donated": "int", "Donation Date": "date"},
            height=12,
        )
        if not rows:
            self._empty_state(body, "No donation records", "No donation records found.")
            return
        for index, row in enumerate(rows):
            donation_id, donor, group, city, units, donation_date = row
            donation_text = donation_date.strftime("%d %b %Y") if hasattr(donation_date, "strftime") else str(donation_date)
            values = (donation_id, donor, group, city, units, donation_text)
            table.insert("", "end", values=values, tags=self._row_tags(values, index))

    def show_reports(self):
        self.active_section = "reports"
        self._set_page_context("Emergency Analytics & Insights", "Mixed chart views for donations, demand, trends, and low-stock risk")
        charts = ctk.CTkFrame(self.content, fg_color="transparent")
        charts.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 14))
        for index in range(2):
            charts.grid_columnconfigure(index, weight=1)
        for row_index in range(4):
            charts.grid_rowconfigure(row_index, weight=1)
        self._chart(charts, "Top Donor Cities", ReportService.top_donor_cities, 0, 0, "bar")
        self._chart(charts, "Most Available Blood Groups", ReportService.most_available_blood_groups, 0, 1, "bar")
        self._chart(charts, "Blood Demand vs Supply", ReportService.blood_demand_vs_supply, 1, 0, "horizontal_bar")
        self._chart(charts, "Requests by Blood Group", ReportService.requests_by_blood_group, 1, 1, "bar")
        self._chart(charts, "Emergency Response Success Rate", ReportService.emergency_response_success_rate, 2, 0, "pie")
        self._chart(charts, "Monthly Donations", ReportService.monthly_donations, 2, 1, "line")
        self._chart(charts, "City Ranking", lambda: [(row[0], row[1] + row[2]) for row in ReportService.city_ranking()], 3, 0, "bar")
        self._chart(charts, "Most Requested Blood Groups", ReportService.most_requested_blood_groups, 3, 1, "bar")

    def _chart(self, parent, title, data_fn, row, col, chart_type):
        card = self._card(parent)
        card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 0))
        ctk.CTkLabel(header, text=title, text_color=PRIMARY, font=("Segoe UI", 16, "bold")).pack(side="left")
        ctk.CTkLabel(header, textvariable=self.last_updated_var, text_color=MUTED, font=("Segoe UI", 10, "bold")).pack(side="right")
        data = self._safe_call(data_fn, [])
        if not data:
            # Show a friendly empty state depending on chart type
            if chart_type == "line":
                self._empty_state(card, "No emergency trend data available yet", "No emergency trend data available yet")
            else:
                self._empty_state(card, "No chart data", "No upgraded emergency-network data available yet.")
            return

        fig = Figure(figsize=(5.0, 3.0), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_facecolor("#FFFFFF")
        fig.patch.set_facecolor("#FFFFFF")

        if chart_type == "pie":
            labels = [str(row[0]) for row in data]
            values = [int(row[1] or 0) if len(row) > 1 else 0 for row in data]
            if not values:
                self._empty_state(card, "No chart data", "No data is available for this chart yet.")
                return
            # dynamic colors based on number of groups
            color_palette = [CRIMSON, ACCENT, WARNING, SUCCESS, CAUTION, PRIMARY, "#F59E0B", "#BE123C"]
            colors_used = color_palette * ((len(values) // len(color_palette)) + 1)
            ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90, colors=colors_used[: len(values)], textprops={"fontsize": 9})
            ax.axis("equal")
        elif chart_type == "line":
            labels = [str(row[1] if len(row) > 1 else row[0]) for row in data]
            values = [int(row[2] or 0) if len(row) > 2 else int(row[1] or 0) for row in data]
            positions = list(range(len(values)))
            ax.plot(positions, values, color=CRIMSON, linewidth=2.5, marker="o")
            ax.fill_between(positions, values, color="#FECACA", alpha=0.35)
            ax.set_xticks(positions)
            ax.set_xticklabels(labels)
            ax.set_ylabel("Requests")
            ax.tick_params(axis="x", labelrotation=25, labelsize=9)
            ax.tick_params(axis="y", labelsize=9)
            ax.grid(alpha=0.2)
        elif chart_type == "horizontal_bar":
            labels = [str(row[0]) for row in data]
            values = [int(row[1] or 0) for row in data]
            annotations = [str(row[2]) if len(row) > 2 else None for row in data]
            # color by severity
            colors_list = []
            for v in values:
                if v == 0:
                    colors_list.append(ALERT)
                elif v < LOW_STOCK_THRESHOLD:
                    colors_list.append(WARNING)
                else:
                    colors_list.append(SUCCESS)
            bars = ax.barh(labels, values, color=colors_list)
            ax.tick_params(axis="y", labelsize=9)
            ax.set_xlabel("Units available")
            # annotate bars
            for index, bar in enumerate(bars):
                w = bar.get_width()
                label = str(int(w))
                if annotations[index] is not None:
                    label = f"{label} | {annotations[index]}"
                ax.text(w + max(0.5, w * 0.01), bar.get_y() + bar.get_height() / 2, label, va='center', fontsize=9)
        else:
            labels = [str(row[0]) for row in data]
            values = [int(row[1] or 0) if len(row) > 1 else int(row[0] or 0) for row in data]
            ax.bar(labels, values, color=CRIMSON)
            ax.tick_params(axis="x", labelrotation=25, labelsize=9)
            ax.set_ylabel("Units / Donors")

        ax.tick_params(axis="y", labelsize=9)
        ax.grid(axis="y", alpha=0.15)
        fig.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
