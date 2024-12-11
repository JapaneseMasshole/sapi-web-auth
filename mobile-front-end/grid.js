"use strict";

export class GridControl {
  constructor(indexes, currency) {
    TableManipulator.initialize();

    // at first, provide initial blank values for indexes and currency
    const emptyValueFunc = (acc, cur) => {
      acc[cur] = {
        price: "N/A",
        marketTime: "N/A",
        netChange: "N/A",
        percentChange: "N/A",
      };
      return acc;
    };

    this._data = {
      indexes: indexes.reduce(emptyValueFunc, {}),
      currency: currency.reduce(emptyValueFunc, {}),
    };

    this.onUpdate(this._data);
  }

  onUpdate(update) {
    const { indexes, currency } = update;

    if (Object.keys(indexes).length > 0) {
      this._updateIndexes(indexes);
    }

    if (Object.keys(currency).length > 0) {
      this._updateCurrencies(currency);
    }
  }

  _updateIndexes(indexes) {
    const sortedData = this._reconcileData("indexes", indexes);
    TableManipulator.updateTable("indexes-table", sortedData);
  }

  _updateCurrencies(currencies) {
    const sortedData = this._reconcileData("currency", currencies);
    TableManipulator.updateTable("currency-table", sortedData);
  }

  // add/remove, then sort and set
  _reconcileData(name, membersChanged) {
    const curData = this._data[name];

    Object.keys(membersChanged).map((ticker) => {
      const ticketUpdateData = membersChanged[ticker];
      curData[ticker] = ticketUpdateData;
    });

    const newData = this._data[name];

    // using some kind of auto-sorted dataset instead of sorting on every update
    // can be more efficient on large data sets, doing this for simplicity
    const table = Object.keys(newData).map((key) => {
      return { name: key, ...newData[key] };
    });

    table.sort((a, b) => {
      if (a.percentChange === "N/A") {
        return true;
      } else if (b.percentChange === "N/A") {
        return false;
      }

      return Math.abs(a.percentChange) < Math.abs(b.percentChange);
    });

    return table;
  }
}

class TableManipulator {
  static initialize() {
    const blankRow = Array(5).fill("");
    const blankRows = Array(5).fill(blankRow);

    const leadersTable = this._createTable([
      ["Index", "Price", "Market Time", "Net Change", "% Change"],
      ...blankRows,
    ]);

    leadersTable.className = "table indexes-table";
    document.querySelector(".main-tables").appendChild(leadersTable);

    const laggersTable = this._createTable([
      ["Currency", "Price", "Market Time", "Net Change", "% Change"],
      ...blankRows,
    ]);

    laggersTable.className = "table currency-table";
    document.querySelector(".main-tables").appendChild(laggersTable);
  }

  // in reality, updating the only changed rows is more efficient,
  // but for simplicity, we will just provide entire table matrix
  static updateTable(tableClassName, data) {
    const table = document.getElementsByClassName(tableClassName)[0];

    const htmlRows = table.getElementsByClassName("row");
    for (let i = 0; i < htmlRows.length; ++i) {
      const htmlRow = htmlRows[i];
      const htmlRowEls = htmlRow.getElementsByClassName("row-item");

      const dataRow = this._objToRow(data[i]);

      // naive check to see if data row was updated
      let dataRowChanged = false;

      for (let j = 0; j < htmlRowEls.length; ++j) {
        const htmlRowEl = htmlRowEls[j];
        const curText = htmlRowEl.innerText;

        if (curText !== dataRow[j].toString()) {
          htmlRowEl.innerText = dataRow[j];

          // do not set on initial update
          if (curText !== "") {
            dataRowChanged = true;
          }
        }
      }

      if (dataRowChanged) {
        htmlRow.className = htmlRow.className + " ticked";
        setTimeout(() => {
          htmlRow.className = htmlRow.className.replace("ticked", "");
        }, 1000);
      }
    }
  }

  static _createTable(matrix) {
    const table = document.createElement("div");

    const headerRowData = matrix[0];
    const dataRows = matrix.slice(1);

    const headerRow = document.createElement("div");
    headerRow.className = "header-row";

    for (const colName of headerRowData) {
      const item = document.createElement("div");
      item.className = "row-item";
      headerRow.appendChild(item);
      item.innerText = colName;
    }

    table.appendChild(headerRow);

    for (const data of dataRows) {
      const row = document.createElement("div");
      row.className = "row";

      for (const itemData of data) {
        const item = document.createElement("div");
        item.className = "row-item";
        row.appendChild(item);
        item.innerText = itemData;
      }

      table.appendChild(row);
    }

    return table;
  }

  static _objToRow(obj) {
    return [
      obj.name,
      obj.percentChange === "N/A" ? "N/A" : obj.price.toFixed(4),
      obj.marketTime,
      obj.netChange === "N/A" ? "N/A" : obj.netChange.toFixed(4),
      obj.percentChange === "N/A" ? "N/A" : obj.percentChange.toFixed(4),
    ];
  }
}
