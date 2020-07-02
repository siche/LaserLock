#ifndef XCON_IMPERIAL_H
#define XCON_IMPERIAL_H

#include <QMainWindow>

namespace Ui {
class XCon_Imperial;
}

class XCon_Imperial : public QMainWindow
{
    Q_OBJECT

public:
    explicit XCon_Imperial(QWidget *parent = nullptr);
    ~XCon_Imperial();

private:
    Ui::XCon_Imperial *ui;
};

#endif // XCON_IMPERIAL_H
