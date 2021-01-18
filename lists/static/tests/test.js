QUnit.test("errors should be hidden on key press", function(assert) {
    initialize();
    $('input[name="text"]').trigger('keypress');
    assert.equal($('.has-error').is(':visible'), false)
});
QUnit.test("errors aren't hidden if there is no keypress", function(assert) {
    initialize();
    assert.equal($('.has-error').is(':visible'), true)
});
