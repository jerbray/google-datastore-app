var app = angular.module('myApp', [], function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});

// app.controller('login', function($scope, $http)
// {
//     $scope.login = function() {
//         $http.post("/login", {username: $scope.username, password: $scope.password});
//     }
// });

app.controller('myCtrl', function($scope, $http)
{
    $scope.isLoading = true;
    $scope.invalid = [false, false, false, false, false];
    $scope.next = false;
    $scope.prev = false;
    $scope.toReturn = [];
    $scope.addToReturn = function (record, edit) {
        record.editType = edit;
        $scope.toReturn.splice(0, 0, record);
    }

    $scope.sort = {
        active: '',
        desc: undefined
    }

    $scope.orderByMe = function(column) {

        var sort = $scope.sort;

        if (sort.active == column) {
            sort.desc = !sort.desc;

        } else {
            sort.active = column;
            sort.desc = false;
        }
        var desc;
        if(sort.desc)
            desc = 'desc';
        else
            desc = 'asc'

        $scope.isLoading = true;
        $http.post("/sort", {'order': column, 'direction': desc});

        $http.get("/get-sort", { headers: { 'Cache-Control' : 'no-cache' } }).then(function(response)
        {
            $scope.isLoading = false;
            $scope.myData = response.data.records;
            console.log(response.data.order);
            console.log(column+desc);
            $scope.next = response.data.next;
            $scope.prev = response.data.prev;
        }, function(response)
        {
            $scope.isLoading = false;
            console.log("Something went wrong");
        });
    };

    $scope.getIcon = function(column) {

        var sort = $scope.sort;

        if (sort.active == column)
        {
            return sort.desc ? 'fa-long-arrow-up' : 'fa-long-arrow-down';
        }

        return 'fa-arrows-v';
    }

    // called by entry "Edit" button
    $scope.deleteEntry = function(x) {
        temp = $scope.myData.indexOf(x);
        deletedEntity = $scope.myData.splice(temp, 1)[0];
        $scope.addToReturn(deletedEntity, "delete");
        $http.post("/save", {records: $scope.toReturn});
        $scope.toReturn = [];
    }

    $scope.editing = null;

    // called by Add Record "Save" button
    $scope.addRecord = function() {
        var record =
            {
                "Year": $scope.yearForm,
                "CauseName": $scope.causeForm,
                "State": $scope.regionForm,
                "Deaths": $scope.deathForm,
                "AgeAdjustedDeathRate": $scope.rateForm
            };
        invalidForm = false;
        if(!$scope.yearForm)
        {
            $scope.invalid[0] = true;
            invalidForm = true;
        }
        if($scope.causeForm == $scope.defaultCause)
        {
            $scope.invalid[1] = true;
            invalidForm = true;
        }
        if($scope.regionForm == $scope.defaultRegion)
        {
            $scope.invalid[2] = true;
            invalidForm = true;
        }
        if(!$scope.deathForm && $scope.deathForm != 0)
        {
            $scope.invalid[3] = true;
            invalidForm = true;
        }
        if(!$scope.rateForm && $scope.rateForm != 0)
        {
            $scope.invalid[4] = true;
            invalidForm = true;
        }
        if(invalidForm)
            return;

        $scope.myData.splice(0, 0, record);
        $scope.addToReturn(record, "add");
        console.log("Saved");
        console.log(record);
        if ($scope.toReturn.length > 0)
        {
            $http.post("/save", {records: $scope.toReturn});
            $scope.toReturn = [];
        }
        $scope.yearForm = "";
        $scope.causeForm = $scope.defaultCause;
        $scope.regionForm = $scope.defaultRegion;
        $scope.deathForm = "";
        $scope.rateForm = "";
        $scope.editing = null;
    }

    // called by entry "Edit" button
    $scope.editRecord = function(x) {
        if ($scope.editing != null)
            $scope.myData.splice(0, 0, $scope.editing);
        temp = $scope.myData.indexOf(x);
        $scope.editing = $scope.myData.splice(temp, 1)[0];

        console.log($scope.editing.Year);
        $scope.yearForm = x.Year;
        $scope.causeForm = x.CauseName;
        $scope.regionForm = x.State;
        $scope.deathForm = x.Deaths;
        $scope.rateForm = x.AgeAdjustedDeathRate;
        console.log($scope.editing);
    }

    $scope.cancelFilter = function() {
        $scope.yearFilter = "";
        $scope.causeFilter = $scope.defaultCause;
        $scope.regionFilter = $scope.defaultRegion;
        $scope.deathFilter = "";
        $scope.rateFilter = "";
    }

    $scope.cancelEdit = function() {
        if ($scope.editing != null)
        {
            $scope.myData.splice(0, 0, $scope.editing);
            $scope.editing = null;
        }
        $scope.invalid = [false, false, false, false, false];
        $scope.yearForm = "";
        $scope.causeForm = $scope.defaultCause;
        $scope.regionForm = $scope.defaultRegion;
        $scope.deathForm = "";
        $scope.rateForm = "";
    }

    $scope.addFilter = function() {
        var filters =  {
            "Year": $scope.yearFilter,
            "CauseName": $scope.causeFilter,
            "State": $scope.regionFilter,
            "Deaths": $scope.deathFilter,
            "AgeAdjustedDeathRate": $scope.rateFilter
        }

        console.log(filters);
        $scope.isLoading = true;
        $http.post("/filter", filters);
        $http.get("/get-sort", { headers: { 'Cache-Control' : 'no-cache' } }).then(function(response)
        {
            $scope.isLoading = false;
            $scope.myData = response.data.records;
            $scope.next = response.data.next;
            $scope.prev = response.data.prev;

        }, function(response)
        {
            $scope.isLoading = false;
            console.log("Something went wrong");
        });
    }

    $scope.clearFilter = function() {
        $scope.yearFilter = "";
        $scope.causeFilter = $scope.defaultCause;
        $scope.regionFilter = $scope.defaultRegion;
        $scope.deathFilter = "";
        $scope.rateFilter = "";

        $scope.addFilter()
    }

    $scope.nextPage = function() {
        console.log("aaaaaaa");
        $scope.isLoading = true;
        $http.get("/next", { headers: { 'Cache-Control' : 'no-cache' } }).then(function(response)
        {
            $scope.isLoading = false;
            $scope.myData = response.data.records;
            $scope.next = response.data.next;
            $scope.prev = response.data.prev;

        }, function(response)
        {
            $scope.isLoading = false;
            console.log("Something went wrong");
        });
    }

    $scope.prevPage = function() {
        console.log("bbbbb");
        $scope.isLoading = true;
        $http.get("/prev", { headers: { 'Cache-Control' : 'no-cache' } }).then(function(response)
        {
            $scope.isLoading = false;
            $scope.myData = response.data.records;
            $scope.next = response.data.next;
            $scope.prev = response.data.prev;

        }, function(response)
        {
            $scope.isLoading = false;
            console.log("Something went wrong");
        });
    }

    $http.get("/data", { headers: { 'Cache-Control' : 'no-cache' } }).then(function(response)
    {
        console.log("Success");
        $scope.isLoading = false;
        $scope.myData = response.data.records;
        $scope.next = response.data.next;
        $scope.prev = response.data.prev;
        $scope.regionList = [];
        $scope.causeList = [];
        for (var i in response.data.regions)
        {
            $scope.regionList.push(response.data.regions[i]);
        }
        for (var i in response.data.causes)
        {
            $scope.causeList.push(response.data.causes[i]);
        }
    //    $scope.orderByMe(['Year', 'CauseName', 'State'])

    }, function(response)
    {
        $scope.isLoading = false;
        console.log("Something went wrong");
    });


});