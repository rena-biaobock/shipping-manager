import angular from 'angular';
import 'angular-mocks';
import '../../app.module';
import './capacity-bar.directive';

describe('capacityBar directive', function() {
  var $compile, $rootScope;

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_$compile_, _$rootScope_) {
    $compile = _$compile_;
    $rootScope = _$rootScope_;
  }));

  function makeBar(used, total) {
    var scope = $rootScope.$new();
    scope.used  = used;
    scope.total = total;
    var el = $compile('<capacity-bar used="used" total="total"></capacity-bar>')(scope);
    scope.$digest();
    return el;
  }

  it('displays 0% when total is 0', function() {
    var el = makeBar(0, 0);
    expect(el[0].querySelector('.bar-pct').textContent.trim()).toBe('0.000%');
  });

  it('displays percentage with 3 decimal places for a whole-number ratio', function() {
    var el = makeBar(27, 100);
    expect(el[0].querySelector('.bar-pct').textContent.trim()).toBe('27.000%');
  });

  it('displays percentage with 3 decimal places for a repeating decimal', function() {
    var el = makeBar(1, 3);
    expect(el[0].querySelector('.bar-pct').textContent.trim()).toBe('33.333%');
  });

  it('caps percentage at 100% when used exceeds total', function() {
    var el = makeBar(50, 10);
    expect(el[0].querySelector('.bar-pct').textContent.trim()).toBe('100.000%');
  });
});
