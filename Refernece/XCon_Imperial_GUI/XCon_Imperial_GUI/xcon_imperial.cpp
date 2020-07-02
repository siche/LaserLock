#include "xcon_imperial.h"
#include "ui_xcon_imperial.h"

XCon_Imperial::XCon_Imperial(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::XCon_Imperial)
{
    ui->setupUi(this);
}

XCon_Imperial::~XCon_Imperial()
{
    delete ui;
}
