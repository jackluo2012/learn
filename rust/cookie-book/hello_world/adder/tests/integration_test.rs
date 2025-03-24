use adder::add_two;

#[test]
fn it_adds_three() {
    let result = add_two(2);
    assert_eq!(result, 6);
}