var dashboardWidget = {

    gridStack: null,

    _selectedCompanyDashboardId: null,

    dashboardInit: function (dashboardAttrObj) {
        this._selectedCompanyDashboardId = dashboardAttrObj.companyDashboardId;
        this._companyWidgetCatlogObj = dashboardAttrObj.widgetCatalogJson;
        this.layoutInit(dashboardAttrObj.widgetCatalogJson, dashboardAttrObj.permissionList, dashboardAttrObj.dashboardLevel);
    },

    layoutInit: function (companyCatlogObj, permissionList, level) {

        var dashboardEditPermission = {
            'companyLevel': 63,
            'factoryLevel': 64,
            'equipmentLevel': 65,
            'admin':0
        }

       
        var showEditOption = function () {

            var modal = '<div class="modal fade" id="add-widget-panel" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">'+
               ' <div class="modal-dialog" role="document">'+
                    '<div class="modal-content">'+
                        '<div class="modal-header">'+
                            '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>'+
                            '<h4 class="modal-title" id="myModalLabel">Add New Widget</h4>'+
                        '</div>'+
                        '<div id="add-widget-content-wrapper" class="modal-body">'+

                            '<div class="dropdown">'+
                                '<button id="display-catlog-select" class="btn btn-default dropdown-toggle" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">'+
                                    '<span id="display-select-text">Select Widget</span>'+
                                    '<span class="caret"></span>'+
                                '</button>'+
                                '<ul id="add-widget-selecter" class="dropdown-menu" aria-labelledby="dropdownMenu1"></ul>'+
                            '</div>'+
                        '</div>'+
                        '<div class="modal-footer">'+
                            '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'+
                            '<button id="add-widget-submit" data-dismiss="modal" type="button" class="btn btn-primary">Submit</button>'+
                        '</div>'+
                    '</div>'+
                '</div>'+
            '</div>';

            var sideButton = '<div class="dashboard-side-btn-wrapper">'+
                '<button id="update-dashboard" type="button" class="btn btn-info side-btn hide-btn" aria-label="Left Align">'+
                    '<span class="glyphicon glyphicon glyphicon glyphicon-floppy-disk" aria-hidden="true"></span>'+
                '</button>'+
                '<button id="add-new-widget" type="button" class="btn btn-info side-btn" aria-label="Left Align" data-toggle="modal" data-target="#add-widget-panel">'+
                    '<span class="glyphicon glyphicon glyphicon-plus" aria-hidden="true"></span>'+
                '</button>'+
                '</div >';

            $('.dashboard-wrapper').prepend(modal);
            var options = "";
            for (var i in companyCatlogObj) {
                options += "<li class=\"widget-catlog\" data-value='" + companyCatlogObj[i].Id + "'><a href=\"#\">" + companyCatlogObj[i].Name + "</a></li>"
            }

            $('#add-widget-selecter').append(options);
            $('#loader-screen').after(sideButton);
            
        };

        var showGridstackEditOption = canEdit(permissionList, dashboardEditPermission, level);
        if (showGridstackEditOption) {
            showEditOption();
        }
        this.gridStackInit(!showGridstackEditOption);
        this.eventBinding();
    },

    gridStackInit: function (hideGridstackEditOption) {
        var options = {
            cellHeight: '20px',
            margin: 10,
            animate: true,
            handle: '.drag-area',
            disableResize: hideGridstackEditOption,
            disableDrag: hideGridstackEditOption

        };

        gridStack = $('.grid-stack').gridstack(options).data('gridstack');
        $('.grid-stack').removeClass('transparent');

    },

    eventBinding: function () {

        var that = this;

        $('#update-dashboard').click(function () {
            that.loadingScreenStart();
            that.updateWidgetLayout();
        });

        $(document).on("click", '.delete-panel-icon', function () {
            var $this = $(this);
            that.removeWidget($this);
        });

        $('#add-widget-selecter').on("click", '.widget-catlog', function () {
            var catlogId = $(this).attr('data-value');
            var displayCatlog = $(this).children().text();
            $('#display-catlog-select').attr('data-id', catlogId).children('#display-select-text').text(displayCatlog);
        });

        $('#add-widget-submit').click(function () {
            that.loadingScreenStart();
            that.addWidget();
        });

        $('.grid-stack').on('change', function (event, items) {
            that.showSaveChange();
        });

    },

    addWidget: function () {

        var catlogId = $('#display-catlog-select').attr('data-id');
        var createDom = '<div class="grid-stack-item fake-new-widget"></div>';

        gridStack.addWidget(createDom, 0, 0, 1, 1, true);

        var newRow = $('.fake-new-widget').attr('data-gs-x');
        var newCol = $('.fake-new-widget').attr('data-gs-y');

        var panelAttriute = {
            'row': newRow,
            'col': newCol,
            'sizeX': 2,
            'sizeY': 2,
            'id': -1,
            'catlogId': catlogId,
        };

        var result = dataValidation(panelAttriute);

        this.DoDashboardWidgetTransactionAjax("addwidgetintodashboard", -1, result.postData, function (error, result) {
            if (error) {
                toastr["error"]("[[[Error]]].");
            } else {
                location.reload();
            }
        });

    },

    removeWidget: function ($this) {

        var _selectPanel = $this.parents(".grid-stack-item");
        var _selectedWidgetId = _selectPanel.attr('data-id');

        if (_selectedWidgetId < 0) {
            toastr["error"]("[[[No Widget Select]]].");
        } else {
            swal({
                title: "[[[Are you sure]]]?",
                text: "",
                type: "error",
                showCancelButton: true,
                confirmButtonClass: 'btn-danger waves-effect waves-light',
                confirmButtonText: '[[[Delete]]]!'
            }, function (isConfirm) {
                    if (isConfirm) {
                        this.loadingScreenStart();
                        this.DoDashboardWidgetTransactionAjax("deletwidgetfromdashboard", _selectedWidgetId, null, function (error, result) {
                            this.loadingScreenFinish();
                            if (error) {
                                toastr["error"]("[[[Error]]].");
                            } else {
                                gridStack.removeWidget(_selectPanel);
                                toastr["success"]("[[[Action Completed]]].");
                            }
                    }.bind(this));
                    
                }
            }.bind(this));
        }
    },

    updateWidgetLayout: function () {

        var postData = new FormData();
        postData.append('dashboardid', this._selectedCompanyDashboardId);
        $('.panel-wrapper').each(function (index, elem) {
            postData.append('widget[' + index + '][rowno]', parseInt($(this).attr('data-gs-x')));
            postData.append('widget[' + index + '][columnseq]', parseInt($(this).attr('data-gs-y')));
            postData.append('widget[' + index + '][widthspace]', parseInt($(this).attr('data-gs-width')));
            postData.append('widget[' + index + '][heightpixel]', parseInt($(this).attr('data-gs-height')));
            postData.append('widget[' + index + '][id]', parseInt($(this).attr('data-id')));
            postData.append('widget[' + index + '][widgetcatalogid]', parseInt($(this).attr('data-widgetcatlogid')));
        });

        this.DoDashboardWidgetTransactionAjax("updatewidgetindashboard", this._selectedCompanyDashboardId, postData, function (error, result) {
            if (error === null) {
                this.loadingScreenFinish();
                $('#update-dashboard').hide();
                toastr["success"]("[[[Action Completed]]].");
            } else {
                console.log('error');
            }
        }.bind(this));
    },
    DoDashboardWidgetTransactionAjax: function (actionName, Id, postData, callback) {

        var that = this;

        var endPoint = "/Setup/ReqAction?action=" + actionName;
        if (postData != null) postData.append('DashboardId', that._selectedCompanyDashboardId);

        if (Id != -1)
            endPoint = endPoint + "&Id=" + Id;
        $.ajax({
            type: "POST",
            url: endPoint + "&t=" + Date.now(),
            data: postData,
            cache: false,
            contentType: false,
            processData: false,
            success: function (data) {

                if (callback) {
                    callback(null, true);
                }

                switch (actionName) {
                    case "getdashboardwidgetbyid":
                        break;
                    default:
                        that.DoDashboardWidgetTransactionAjax("getdashboardwidgetbyid", that._selectedCompanyDashboardId, null);
                        _selectedWidgetId = -1;
                        break;
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {

                console.log('ajax failed');

                if (callback) {
                    callback(true, null);
                }

                if (XMLHttpRequest.status == 401) {
                    toastr["error"]("[[[Session Expired. Please Re-Login]]].");
                    setTimeout(function () { sfBacktoHomeIndex(); }, 2000);
                }
                else
                    toastr["error"]("Error");
            }
        });
    },

    showSaveChange: function () {
        $('#update-dashboard').show();
    },

    loadingScreenStart: function () {
        $('#loader-screen').fadeIn();
    },

    loadingScreenFinish: function () {
        $('#loader-screen').fadeOut();
    }

};

function canEdit(permissionList, dashboardEditPermission, level)
{
    var permissions = permissionList.toString().split(",");
    for (i = 0; i < permissions.length; i++) {
        if (permissions[i] == dashboardEditPermission.admin)
            return true;
    } 
    switch (level) {
        //company level
        case 0:
            for (i = 0; i < permissions.length; i++) {
                if (permissions[i] == dashboardEditPermission.companyLevel)
                    return true;
            }
            break;
        //Factory level
        case 1:
            for (i = 0; i < permissions.length; i++) {
                if (permissions[i] == dashboardEditPermission.factoryLevel)
                    return true;
            }
            break;
        //Equipment level
        case 2:
            for (i = 0; i < permissions.length; i++) {
                if (permissions[i] == dashboardEditPermission.equipmentLevel)
                    return true;
            }
            break;
        default:
            return false;
    }
    return false;
}


function dataValidation(panelAttriute) {

    var postData = new FormData();

    if (panelAttriute.row !== null && panelAttriute.row !== undefined) {
        postData.append('RowNo', panelAttriute.row);
    } else {
        swal("[[[Invalid]]] !", "[[[Row No]]] [[[is necessary]]].");
        return {
            postData: postData,
            id: panelAttriute.id,
            isValidated: false
        };
    }
    if (panelAttriute.col !== null && panelAttriute.col !== undefined) {
        postData.append('ColumnSeq', panelAttriute.col);
    } else {
        swal("[[[Invalid]]] !", "[[[Column No]]] [[[is necessary]]].");
        return {
            postData: postData,
            id: panelAttriute.id,
            isValidated: false
        };
    }

    if (panelAttriute.catlogId !== 0) {
        postData.append('WidgetCatalogId', panelAttriute.catlogId);
    } else {
        swal("[[[Invalid]]] !", "[[[Widget]]] [[[is necessary]]].");
        return {
            postData: postData,
            id: panelAttriute.id,
            isValidated: false
        };
    }

    if (panelAttriute.sizeX !== 0) {
        postData.append('WidthSpace', panelAttriute.sizeX);
    } else {
        swal("[[[Invalid]]] !", "[[[Width Space]]] [[[is necessary]]].");
        return {
            postData: postData,
            id: panelAttriute.id,
            isValidated: false
        };
    }

    if (panelAttriute.sizeY !== 0) {
        postData.append('HeightPixel', panelAttriute.sizeY);
    } else {
        swal("[[[Invalid]]] !", "[[[Height Pixel]]] [[[is necessary]]].");
        return {
            postData: postData,
            id: panelAttriute.id,
            isValidated: false
        };
    }

    return {
        postData: postData,
        id: panelAttriute.id,
        companyDashBoardId: panelAttriute.companyDashBoardId,
        isValidated: true
    }
}