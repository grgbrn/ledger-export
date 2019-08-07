import extract
import unittest

class TestParseLedger(unittest.TestCase):

    def test_sample1(self):
        expected = [
            ('Expenses:Cash', '$90.00'),
            ('Expenses:Cash', '450.00 EUR'),
            ('Expenses:Clothing', '74.95 EUR'),
            ('Expenses:Computer:Hardware', '$446.23'),
            ('Expenses:Computer:Hosting', '$8.50'),
            ('Expenses:Computer:Services', '$43.98'),
            ('Expenses:Dining', '23.80 EUR'),
            ('Expenses:Electronics', '9.99 EUR'),
            ('Expenses:Entertainment', '27.50 EUR'),
            ('Expenses:Groceries', '136.03 EUR'),
            ('Expenses:HOA', '$515.52'),
            ('Expenses:Health', '$75.21'),
            ('Expenses:Household', '$66.04'),
            ('Expenses:Household', '19.40 EUR'),
            ('Expenses:Insurance:Condo', '$53.18'),
            ('Expenses:Insurance:Health', '$615.31'),
            ('Expenses:Mortgage', '$1,984.53'),
            ('Expenses:Music', '$9.99'),
            ('Expenses:Rent', '$650.00'),
            ('Expenses:Subscriptions', '$14.98'),
            ('Expenses:Transport:Bikeshare', '4.00 EUR'),
            ('Expenses:Transport:Transit', '$1.79'),
            ('Expenses:Transport:Transit', '59.10 EUR'),
            ('Expenses:Travel:Flight', '$143.90'),
            ('Expenses:Utilities:Electric', '$47.80'),
            ('Expenses:Utilities:Mobile', '$60.00'),
            ('Expenses:Utilities:Mobile', '5.00 EUR'),
        ]

        # parse_ledger_output(output: bytes) -> Dict[str, str]:
        with open('test/sample1', 'rb') as f:
            buf = f.read()
            result = extract.parse_ledger_output(buf)

            self.assertEqual(len(result), len(expected))

            # this depends on order being preserved
            for out, check in zip(result, expected):
                # print(out, check)
                self.assertEqual(out, check)


if __name__ == '__main__':
    unittest.main()