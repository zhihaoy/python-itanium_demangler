import pytest

from itanium_demangler import parse, mangle
from itanium_demangler import _operators, _unary_operators, _builtin_types


def assert_parses(mangled, ast):
    result = parse(mangled)
    assert result == ast


def assert_demangles(mangled, demangled):
    """Asserts that a mangled name demangles to the expected string."""
    result = parse(mangled)
    if result is not None:
        result = str(result)
    assert result == demangled


def assert_roundtrip(mangled, demangled):
    """Asserts demangling and that the parsed AST mangles back to the original."""
    result = parse(mangled)
    if result is not None:
        assert mangle(result) == mangled
        result = str(result)
    assert result == demangled


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z3foo', 'foo'),
    ('_Z3x', None),
])
def test_name(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_ZN3fooC1E', 'foo::{ctor}'),
    ('_ZN3fooC2E', 'foo::{base ctor}'),
    ('_ZN3fooC3E', 'foo::{allocating ctor}'),
    ('_ZN3fooD0E', 'foo::{deleting dtor}'),
    ('_ZN3fooD1E', 'foo::{dtor}'),
    ('_ZN3fooD2E', 'foo::{base dtor}'),
    ('_ZN3fooC1IcEEc', 'foo::{ctor}<char>(char)'),
    ('_ZN3fooD1IcEEc', 'foo::{dtor}<char>(char)'),
])
def test_ctor_dtor(mangled, demangled):
    assert_roundtrip(mangled, demangled)


# Create a list of operators for parameterization, coping with special cases
_any_operators = dict(_operators, **_unary_operators)
_operator_tests = [
    (op, 'operator' + _any_operators[op]) for op in _any_operators
    if _any_operators[op] not in ['new', 'new[]', 'delete', 'delete[]']
] + [
    ('nw', 'operator new'),
    ('na', 'operator new[]'),
    ('dl', 'operator delete'),
    ('da', 'operator delete[]'),
]


@pytest.mark.parametrize("op_code, op_str", _operator_tests)
def test_operators(op_code, op_str):
    assert_roundtrip('_Z' + op_code, op_str)


def test_operator_cast():
    assert_roundtrip('_Zcvi', 'operator int')


@pytest.mark.parametrize("mangled, demangled", [
    ('_ZSt3foo', 'std::foo'),
    ('_ZNSt3sub3fooE', 'std::sub::foo'),
    ('_ZSs', 'std::string'),
    ('_Z3fooISt6vectorE', 'foo<std::vector>'),
    ('_Z3fooINSt3__19allocatorIcEEE', 'foo<std::__1::allocator<char>>'),
    ('_ZSaIhE', 'std::allocator<unsigned char>'),
])
def test_std_substs(mangled, demangled):
    assert_roundtrip(mangled, demangled)


def test_std_substs_none():
    assert_parses('_ZSt', None)


@pytest.mark.parametrize("mangled, demangled", [
    ('_ZN3fooE', 'foo'),
    ('_ZN3foo5bargeE', 'foo::barge'),
    ('_ZN3fooIcE5bargeE', 'foo<char>::barge'),
    ('_ZNK3fooE', 'foo const'),
    ('_ZNV3fooE', 'foo volatile'),
    ('_ZNKR3fooE', 'foo const &'),
    ('_ZNKO3fooE', 'foo const &&'),
])
def test_nested_name(mangled, demangled):
    if demangled.isalnum():
        assert_demangles(mangled, demangled)
    else:
        assert_roundtrip(mangled, demangled)


def test_nested_name_none():
    assert_parses('_ZNKO3foo', None)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z3fooIcE', 'foo<char>'),
    ('_ZN2ns3fooIcEE', 'ns::foo<char>'),
])
def test_template_args(mangled, demangled):
    assert_roundtrip(mangled, demangled)


def test_template_args_none():
    assert_parses('_Z3fooI', None)


@pytest.mark.parametrize("type_code, type_node", _builtin_types.items())
def test_builtin_types(type_code, type_node):
    mangled = '_Z1fI' + type_code + 'E'
    demangled = 'f<' + str(type_node) + '>'
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fIriE', 'f<int restrict>'),
    ('_Z1fIKiE', 'f<int const>'),
    ('_Z1fIViE', 'f<int volatile>'),
    ('_Z1fIKViE', 'f<int const volatile>'),
])
def test_qualified_type(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fv', 'f()'),
    ('_Z1fi', 'f(int)'),
    ('_Z1fic', 'f(int, char)'),
    ('_Z1fic', 'f(int, char)'),
    ('_Z1fIEic', 'int f<>(char)'),
    ('_ZN1fIEC1Eic', 'f<>::{ctor}(int, char)'),
])
def test_function_type(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fIPiE', 'f<int*>'),
    ('_Z1fIPPiE', 'f<int**>'),
    ('_Z1fIRiE', 'f<int&>'),
    ('_Z1fIOiE', 'f<int&&>'),
    ('_Z1fIKRiE', 'f<int& const>'),
    ('_Z1fIRKiE', 'f<int const&>'),
])
def test_indirect_type(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fILi1EE', 'f<(int)1>'),
    ('_Z1fIL_Z1gEE', 'f<g>'),
])
def test_literal(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fILb0EJciEE', 'f<(bool)0, char, int>'),
    ('_Z1fILb0EIciEE', 'f<(bool)0, char, int>'),
    ('_Z1fIJciEEvDpOT_', 'void f<char, int>(char, int)'),
    ('_Z1fIIciEEvDpOT_', 'void f<char, int>(char, int)'),
])
def test_argpack(mangled, demangled):
    assert_demangles(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_ZTV1f', 'vtable for f'),
    ('_ZTT1f', 'vtt for f'),
    ('_ZTI1f', 'typeinfo for f'),
    ('_ZTS1f', 'typeinfo name for f'),
    ('_ZThn16_1fv', 'non-virtual thunk for f()'),
    ('_ZTv16_8_1fv', 'virtual thunk for f()'),
    ('_ZGV1f', 'guard variable for f'),
    ('_ZGTt1fv', 'transaction clone for f()'),
])
def test_special(mangled, demangled):
    assert_demangles(mangled, demangled)


def test_template_param():
    assert_demangles('_ZN1fIciEEvT_PT0_', 'void f<char, int>(char, int*)')


def test_template_param_none():
    assert_parses('_ZN1fIciEEvT_PT0', None)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z3fooIEvS_', 'void foo<>(foo)'),
    ('_ZN3foo3barIES_E', 'foo::bar<>::foo'),
    ('_ZN3foo3barIES0_E', 'foo::bar<>::foo::bar'),
    ('_ZN3foo3barIES1_E', 'foo::bar<>::foo::bar<>'),
    ('_Z3fooIS_E', 'foo<foo>'),
    ('_ZSt3fooIS_E', 'std::foo<std::foo>'),
    ('_Z3fooIPiEvS0_', 'void foo<int*>(int*)'),
    ('_Z3fooISaIcEEvS0_',
     'void foo<std::allocator<char>>(std::allocator<char>)'),
    ('_Z3fooI3barS0_E', 'foo<bar, bar>'),
    ('_ZN2n11fEPNS_1bEPNS_2n21cEPNS2_2n31dE',
     'n1::f(n1::b*, n1::n2::c*, n1::n2::n3::d*)'),
    ('_ZN1f1gES_IFvvEE', 'f::g(f<void ()>)'),
    ('_ZplIcET_S0_', 'char operator+<char>(char)'),
])
def test_substitution(mangled, demangled):
    assert_demangles(mangled, demangled)


@pytest.mark.parametrize("mangled", [
    '_ZN3foo3barIES_ES2_',
    '_ZplIcET_S1_',
    '_ZStplIcEvS0_',
])
def test_substitution_none(mangled):
    assert_parses(mangled, None)


def test_abi_tag():
    assert_roundtrip('_Z3fooB5cxx11v', 'foo[abi:cxx11]()')
    assert_roundtrip('_Z1AB3barB3foo', 'A[abi:bar][abi:foo]')


def test_const():
    assert_demangles('_ZL3foo', 'foo')


@pytest.mark.parametrize("mangled, demangled", [
    ('_ZmiIiE', 'operator-<int>'),
    ('_ZmiIiEvv', 'void operator-<int>()'),
    ('_ZmiIiEvKT_RT_', 'void operator-<int>(int const, int&)'),
    ('_ZcviIiE', 'operator int<int>'),
    ('_ZcviIiEv', 'operator int<int>()'),
    ('_ZcviIiET_T_', 'operator int<int>(int, int)'),
])
def test_operator_template(mangled, demangled):
    if 'T' in mangled:
        assert_demangles(mangled, demangled)
    else:
        assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fA1_c', 'f(char[(int)1])'),
    ('_Z1fRA1_c', 'f(char(&)[(int)1])'),
    ('_Z1fIA1_cS0_E', 'f<char[(int)1], char[(int)1]>'),
])
def test_array(mangled, demangled):
    if 'S' in mangled:
        assert_demangles(mangled, demangled)
    else:
        assert_roundtrip(mangled, demangled)


def test_array_none():
    assert_parses('_Z1fA1c', None)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fFvvE', 'f(void ())'),
    ('_Z1fPFvvE', 'f(void (*)())'),
    ('_Z1fPPFvvE', 'f(void (**)())'),
    ('_Z1fRPFvvE', 'f(void (*&)())'),
    ('_Z1fKFvvE', 'f(void () const)'),
])
def test_function(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled",
                         [('_Z1fM3fooi', 'f(int foo::*)'),
                          ('_Z1fMN3foo3barEi', 'f(int foo::bar::*)'),
                          ('_Z1fM3fooN3bar1XE', 'f(bar::X foo::*)'),
                          ('_Z1fM3fooIcE3bar', 'f(bar foo<char>::*)'),
                          ('_Z1fM3foo3barIlE', 'f(bar<long> foo::*)'),
                          ('_Z3fooPM2ABi', 'foo(int AB::**)')])
def test_member_data(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z1fM3fooFvvE', 'f(void (foo::*)())'),
    ('_Z1fMN3foo3barEFvvE', 'f(void (foo::bar::*)())'),
    ('_Z3fooRM3barFviE', 'foo(void (bar::*&)(int))'),
])
def test_member_function(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_Z3fooIRKN5boost2lsEEiv', 'int foo<boost::ls const&>()'),
    ('_ZNKR5boost2ls5memfnEv', 'boost::ls::memfn() const &'),
    ('_Z3da2IL_Z4wellEEiv', 'int da2<well>()'),
    ('_ZNSt6thread4joinEv', 'std::thread::join()'),
])
def test_calls(mangled, demangled):
    assert_roundtrip(mangled, demangled)


@pytest.mark.parametrize("mangled, demangled", [
    ('_ZNKSt8valarrayIiE4sizeEv', 'std::valarray<int>::size() const'),
    ('_ZNSt6vectorIiSaIiEED1Ev',
     'std::vector<int, std::allocator<int>>::{dtor}()'),
])
def test_std_substs_nested(mangled, demangled):
    assert_roundtrip(mangled, demangled)
