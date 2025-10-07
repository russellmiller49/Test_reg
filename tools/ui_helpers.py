"""Reusable UI helpers for tri-state gating."""

from typing import Any, Iterable, List, Optional, Tuple

import streamlit as st

TriState = Tuple[Optional[bool], str, str]


def tri_state(label: str, key: str) -> TriState:
    """
    Tri-state radio returning (value, status, detail).

    value: True|False|None
    status: 'present'|'explicit_no'|'not_documented'
    detail: optional reason ('unsure' if None by user choice)
    """
    choice = st.radio(label, ["Yes", "No", "Unsure"], horizontal=True, key=key)
    if choice == "Yes":
        return True, "present", ""
    if choice == "No":
        return False, "explicit_no", ""
    return None, "not_documented", "unsure"


def gated_number(
    label: str,
    key: str,
    show: bool,
    *,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    step: Optional[float] = 1.0,
    default: Optional[float] = None,
) -> Optional[float]:
    if not show:
        return None
    value = st.number_input(
        label,
        min_value=min_value,
        max_value=max_value,
        step=step,
        value=default,
        key=key,
    )
    return float(value)


def gated_int(
    label: str,
    key: str,
    show: bool,
    *,
    min_value: int = 0,
    max_value: int = 100,
    step: int = 1,
    default: Optional[int] = None,
) -> Optional[int]:
    if not show:
        return None
    value = st.number_input(
        label,
        min_value=min_value,
        max_value=max_value,
        step=step,
        value=default if default is not None else min_value,
        key=key,
    )
    return int(value)


def gated_text(label: str, key: str, show: bool, default: str = "") -> Optional[str]:
    if not show:
        return None
    value = st.text_input(label, value=default, key=key)
    return value or None


def gated_text_area(
    label: str,
    key: str,
    show: bool,
    default: str = "",
    height: int = 120,
) -> Optional[str]:
    if not show:
        return None
    value = st.text_area(label, value=default, key=key, height=height)
    return value or None


def gated_select(
    label: str,
    key: str,
    options: Iterable[Any],
    show: bool,
    *,
    index: int = 0,
) -> Optional[Any]:
    if not show:
        return None
    return st.selectbox(label, list(options), index=index, key=key)


def gated_multiselect(
    label: str,
    key: str,
    options: Iterable[Any],
    show: bool,
    default: Optional[List[Any]] = None,
) -> List[Any]:
    if not show:
        return []
    return st.multiselect(label, list(options), default or [], key=key)
