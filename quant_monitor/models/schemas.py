"""Dataframe schemas via Pandera to rigorously enforce matrix invariants."""


import pandas as pd
import pandera as pa
from pandera.typing import Series


class CleanPricesSchema(pa.SchemaModel):
    """Schema ensuring our incoming closing prices are matrix-ready."""

    # Ensuring standard dimensions. No nulls allowed!
    class Config:
        strict = False  # Allows additional ticker columns dynamically
        coerce = True  # Attmepts to force floats

    # We validate index dynamically in functions, but want to ensure it's a DatetimeIndex

    @pa.dataframe_check
    def check_index_type(cls, df: pd.DataFrame) -> bool:
        return isinstance(df.index, pd.DatetimeIndex)

    @pa.dataframe_check
    def check_no_missing_data(cls, df: pd.DataFrame) -> bool:
        """Matrix inversion crashes if NaNs exist. Block them natively."""
        return df.isna().sum().sum() == 0


class ReturnsMatrixSchema(pa.SchemaModel):
    """Schema ensuring our calculated returns are strictly float and bounded."""

    class Config:
        strict = False
        coerce = True

    @pa.dataframe_check
    def check_no_infinities(cls, df: pd.DataFrame) -> bool:
        import numpy as np

        return not np.isinf(df.values).any()


class FactorRegressionSchema(pa.SchemaModel):
    """Ensure Fama-French merged inputs correctly align dates before regression."""

    Mkt_RF: Series[float] = pa.Field(alias="Mkt-RF", nullable=False)
    SMB: Series[float] = pa.Field(nullable=False)
    HML: Series[float] = pa.Field(nullable=False)
    RF: Series[float] = pa.Field(nullable=False)
    # We might have Momentum:
    Mom: Series[float] = pa.Field(nullable=True, required=False)

    @pa.dataframe_check
    def check_index_type(cls, df: pd.DataFrame) -> bool:
        return isinstance(df.index, pd.DatetimeIndex)
