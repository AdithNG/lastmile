"""initial schema

Revision ID: e5107eead70d
Revises:
Create Date: 2026-02-27 11:43:49.031752

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5107eead70d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "depots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_depots_id", "depots", ["id"], unique=False)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("depot_id", sa.Integer(), nullable=False),
        sa.Column("capacity_kg", sa.Float(), nullable=False),
        sa.Column("driver_name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["depot_id"], ["depots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicles_id", "vehicles", ["id"], unique=False)

    op.create_table(
        "stops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("earliest_time", sa.Time(), nullable=False),
        sa.Column("latest_time", sa.Time(), nullable=False),
        sa.Column("package_weight_kg", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "in_route", "delivered", "failed", name="stopstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stops_id", "stops", ["id"], unique=False)

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_distance_km", sa.Float(), nullable=True),
        sa.Column("total_time_min", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routes_id", "routes", ["id"], unique=False)

    op.create_table(
        "route_stops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("stop_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("planned_arrival", sa.String(), nullable=True),
        sa.Column("actual_arrival", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_route_stops_id", "route_stops", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_route_stops_id", table_name="route_stops")
    op.drop_table("route_stops")
    op.drop_index("ix_routes_id", table_name="routes")
    op.drop_table("routes")
    op.drop_index("ix_stops_id", table_name="stops")
    op.drop_table("stops")
    op.execute("DROP TYPE IF EXISTS stopstatus")
    op.drop_index("ix_vehicles_id", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index("ix_depots_id", table_name="depots")
    op.drop_table("depots")
