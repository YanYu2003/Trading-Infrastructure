from mini_trading.app.cli_demo import write_demo_sqlite
from mini_trading.app.run_history import main


def _demo_db(tmp_path):
    db_path = tmp_path / "demo.sqlite"
    write_demo_sqlite(db_path)
    return db_path


def test_list_runs_outputs_saved_run(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "list-runs"])

    output = capsys.readouterr().out
    assert (
        "run_id,events_processed,signal_count,order_count,fill_count,"
        "snapshot_count,final_equity,realized_pnl,unrealized_pnl"
    ) in output
    assert "demo,4,2,2,2,4,100120,120,0" in output


def test_show_run_outputs_single_run_summary(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "show-run", "demo"])

    output = capsys.readouterr().out
    assert (
        "run_id,created_at,events_processed,signal_count,order_count,fill_count,"
        "snapshot_count,final_cash,final_gross_market_value,final_equity,"
        "realized_pnl,unrealized_pnl"
    ) in output
    assert "demo," in output
    assert ",4,2,2,2,4,100120,0,100120,120,0" in output


def test_orders_outputs_order_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "orders", "demo"])

    output = capsys.readouterr().out
    assert (
        "order_id,symbol,side,order_type,quantity,limit_price,"
        "filled_quantity,status,created_at"
    ) in output
    assert "ord-1,AAPL,buy,market,10,,10,filled," in output
    assert "ord-2,AAPL,sell,market,10,,10,filled," in output


def test_fills_outputs_fill_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "fills", "demo"])

    output = capsys.readouterr().out
    assert "fill_id,order_id,symbol,side,price,quantity,notional,timestamp" in output
    assert "ord-1-fill-1,ord-1,AAPL,buy,99,10,990," in output
    assert "ord-2-fill-2,ord-2,AAPL,sell,111,10,1110," in output


def test_snapshots_outputs_account_snapshot_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "snapshots", "demo"])

    output = capsys.readouterr().out
    assert (
        "snapshot_index,cash,gross_market_value,equity,"
        "realized_pnl,unrealized_pnl"
    ) in output
    assert "0,100000,0,100000,0,0" in output
    assert "2,99010,1060,100070,0,70" in output
    assert "3,100120,0,100120,120,0" in output


def test_positions_outputs_position_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "positions", "demo"])

    output = capsys.readouterr().out
    assert (
        "snapshot_index,symbol,quantity,average_cost,last_price,"
        "market_value,unrealized_pnl"
    ) in output
    assert "1,AAPL,10,99,99,990,0" in output
    assert "2,AAPL,10,99,106,1060,70" in output


def test_positions_can_filter_by_snapshot_index(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "positions", "demo", "--snapshot-index", "2"])

    output = capsys.readouterr().out
    assert "2,AAPL,10,99,106,1060,70" in output
    assert "1,AAPL,10,99,99,990,0" not in output
