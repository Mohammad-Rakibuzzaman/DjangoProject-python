from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from transactions.constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID
from datetime import datetime
from django.db.models import Sum
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
    TransferForm,
)
from transactions.models import Transaction, TransferTransaction
from accounts.models import UserBankAccount

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # template e context data pass kora
        context.update({
            'title': self.title
        })

        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        # if not account.initial_deposit_date:
        #     now = timezone.now()
        #     account.initial_deposit_date = now
        account.balance += amount # amount = 200, tar ager balance = 0 taka new balance = 0+200 = 200
        account.save(
            update_fields=[
                'balance'
            ]
        )

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )

        return super().form_valid(form)


# class WithdrawMoneyView(TransactionCreateMixin):
#     form_class = WithdrawForm
#     title = 'Withdraw Money'

#     def get_initial(self):
#         initial = {'transaction_type': WITHDRAWAL}
#         return initial

#     def form_valid(self, form):
#         amount = form.cleaned_data.get('amount')

#         self.request.user.account.balance -= form.cleaned_data.get('amount')
#         # balance = 300
#         # amount = 5000
#         self.request.user.account.save(update_fields=['balance'])

#         messages.success(
#             self.request,
#             f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
#         )

#         return super().form_valid(form)
    

# class WithdrawMoneyView(TransactionCreateMixin):
#     form_class = WithdrawForm
#     title = 'Withdraw Money'

#     def get_initial(self):
#         initial = {'transaction_type': WITHDRAWAL}
#         return initial

#     def form_valid(self, form):
#         user_account = self.request.user.account

#         if user_account.is_bankrupt:
#             messages.error(self.request, 'Your account is marked as bankrupt. Withdrawal is not allowed.')
#             return redirect('home')

#         amount = form.cleaned_data.get('amount')
#         user_account.balance -= form.cleaned_data.get('amount')
#         user_account.save(update_fields=['balance'])

#         messages.success(
#             self.request,
#             f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
#         )

#         return super().form_valid(form)
    
class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        user_account = self.request.user.account

        if not user_account.is_bankrupt:  # Check if the bank is bankrupt
            if amount <= user_account.balance:  # Check if there's enough balance
                user_account.balance -= amount
                user_account.save(update_fields=['balance'])

                messages.success(
                    self.request,
                    f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
                )
                return super().form_valid(form)

            messages.error(
                self.request,
                f'Insufficient funds. You have {user_account.balance} $ in your account.'
            )
        else:
            messages.error(
                self.request,
                'The bank is bankrupt. Withdrawals are not allowed at the moment.'
            )

        return redirect('home')




class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account,transaction_type=3,loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )

        return super().form_valid(form)
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0 # filter korar pore ba age amar total balance ke show korbe
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct() # unique queryset hote hobe
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })

        return context
    
        
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
                # Reduce the loan amount from the user's balance
                # 5000, 500 + 5000 = 5500
                # balance = 3000, loan = 5000
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(
            self.request,
            f'Loan amount is greater than available balance'
        )

        return redirect('loan_list')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans' # loan list ta ei loans context er moddhe thakbe
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=3)
        print(queryset)
        return queryset
    

# class TransferMoneyView(View):
#     template_name = 'transactions/transfer_money.html'

#     def get(self, request):
#         form = TransferForm()
#         return render(request, self.template_name, {'form': form})
    
#     def post(self, request):
#         form = TransferForm(request.POST)
#         if form.is_valid():
#             sender_account = request.user.account
#             receiver_account = form.cleaned_data['receiver']
#             amount = form.cleaned_data['amount']


#             if receiver_account:
#                 if sender_account.balance >= amount:
#                     sender_account.balance -= amount 
#                     receiver_account.balance += amount

#                     sender_account.save(update_fields=['balance'])
#                     receiver_account.save(update_fields=['balance'])

#                     TransferTransaction.objects.create(sender=sender_account, receiver=receiver_account, amount=amount)

#                     messages.success(request, f'Successfully transferred {"{:,.2f}".format(float(amount))}$ to {receiver_account.user.username}')
#                 else:
#                     messages.error(request, f'Insufficient funds for the transfer.')

#             else:
#                 messages.error(request, 'Receiver account not found.')

#             return redirect('transfer_money')  
        
#         return render(request, self.template_name, {'form': form})
    
class TransferMoneyView(View):
    template_name = 'transactions/transfer_money.html'

    def get(self, request):
        form = TransferForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = TransferForm(request.POST)
        if form.is_valid():
            sender_account = request.user.account
            account_number = form.cleaned_data['account_number']
            amount = form.cleaned_data['amount']

            try:
                receiver_account = UserBankAccount.objects.get(account_no=account_number)
            except UserBankAccount.DoesNotExist:
                messages.error(request, f'Receiver account with account number {account_number} not found.')
                return redirect('transfer_money')

            if sender_account.balance >= amount:
                sender_account.balance -= amount
                receiver_account.balance += amount

                sender_account.save(update_fields=['balance'])
                receiver_account.save(update_fields=['balance'])

                TransferTransaction.objects.create(sender=sender_account, receiver=receiver_account, amount=amount)

                messages.success(request, f'Successfully transferred {"{:,.2f}".format(float(amount))}$ to {receiver_account.user.username}')
            else:
                messages.error(request, 'Insufficient funds for the transfer.')
            
            return redirect('transfer_money')

        return render(request, self.template_name, {'form': form})